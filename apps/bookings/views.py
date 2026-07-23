from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from .models import Booking, Approval
from .forms import BookingCreateForm, RecommendationForm, ApprovalForm, RejectionForm, CancelForm
from .services import BookingService, ConflictChecker, RecommendationService, RecommendationRequest, ApprovalService, StatisticsService
from apps.venues.models import Room


class BookingListView(LoginRequiredMixin, ListView):
    """我的预约列表"""
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Booking.Status.choices
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    """预约详情"""
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class BookingCreateView(LoginRequiredMixin, CreateView):
    """创建预约"""
    model = Booking
    form_class = BookingCreateForm
    template_name = 'bookings/booking_create.html'
    success_url = reverse_lazy('bookings:booking_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取场地信息
        venue_id = self.request.GET.get('venue')
        if venue_id:
            context['venue'] = get_object_or_404(Room, pk=venue_id)
        
        context['conflicts'] = self.request.session.pop('booking_conflicts', [])
        context['equipment_warning'] = self.request.session.pop('equipment_warning', None)
        
        return context
    
    def form_valid(self, form):
        # 获取场地
        venue_id = self.request.GET.get('venue')
        if not venue_id:
            messages.error(self.request, '请选择场地')
            return redirect('venues:room_list')
        
        venue = get_object_or_404(Room, pk=venue_id)
        
        # 获取表单数据
        cleaned_data = form.cleaned_data
        # required_equipments不在表单中，使用空列表
        required_equipments = []
        
        # 创建预约
        result = BookingService.create_booking(
            user=self.request.user,
            venue=venue,
            title=cleaned_data['title'],
            booking_type=cleaned_data['booking_type'],
            start_time=cleaned_data['start_time'],
            end_time=cleaned_data['end_time'],
            participant_count=cleaned_data['participant_count'],
            required_equipments=required_equipments,
            contact_name=cleaned_data.get('contact_name'),
            contact_phone=cleaned_data.get('contact_phone'),
            remark=cleaned_data.get('remark')
        )
        
        if result['success']:
            messages.success(self.request, f'预约提交成功！预约编号：{result["booking"].booking_no}')
            
            # 如果有设备警告，显示提示
            if result.get('equipment_warning'):
                messages.warning(self.request, result['equipment_warning'])
            
            return redirect('bookings:booking_detail', pk=result['booking'].pk)
        else:
            # 保存冲突信息到session（需要序列化datetime对象）
            serialized_conflicts = []
            for conflict in result['conflicts']:
                serialized_conflict = {
                    'type': conflict.get('type'),
                    'message': conflict.get('message'),
                }
                # 序列化detail中的datetime对象
                detail = conflict.get('detail', {})
                if detail:
                    serialized_detail = {}
                    for key, value in detail.items():
                        if hasattr(value, 'strftime'):
                            serialized_detail[key] = value.strftime('%Y-%m-%d %H:%M')
                        else:
                            serialized_detail[key] = value
                    serialized_conflict['detail'] = serialized_detail
                serialized_conflicts.append(serialized_conflict)
            
            self.request.session['booking_conflicts'] = serialized_conflicts
            if result.get('equipment_warning'):
                self.request.session['equipment_warning'] = result['equipment_warning']
            
            # 构建错误消息
            conflict_messages = [c['message'] for c in result['conflicts']]
            messages.error(self.request, '预约失败：' + '；'.join(conflict_messages))
            
            return redirect(self.request.path + f'?venue={venue_id}')


@login_required
def check_availability(request):
    """检查预约可用性（AJAX）"""
    if request.method == 'POST':
        import json
        from django.utils.dateparse import parse_datetime
        
        data = json.loads(request.body)
        
        venue_id = data.get('venue_id')
        start_time = parse_datetime(data.get('start_time'))
        end_time = parse_datetime(data.get('end_time'))
        participant_count = data.get('participant_count')
        required_equipments = data.get('required_equipments', [])
        
        venue = get_object_or_404(Room, pk=venue_id)
        
        result = BookingService.check_booking_availability(
            venue=venue,
            start_time=start_time,
            end_time=end_time,
            user=request.user,
            participant_count=participant_count,
            required_equipments=required_equipments
        )
        
        return JsonResponse(result)
    
    return JsonResponse({'error': 'Invalid request method'})


@login_required
def cancel_booking(request, pk):
    """取消预约"""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if booking.status not in [Booking.Status.PENDING, Booking.Status.APPROVED]:
        messages.error(request, '该预约不可取消')
        return redirect('bookings:booking_detail', pk=pk)
    
    # 检查是否在开始前2小时内
    if booking.start_time <= timezone.now() + timezone.timedelta(hours=2):
        messages.error(request, '预约开始前2小时内不能取消')
        return redirect('bookings:booking_detail', pk=pk)
    
    if request.method == 'POST':
        booking.status = Booking.Status.CANCELLED
        booking.save()
        messages.success(request, '预约已取消')
        return redirect('bookings:booking_list')
    
    return render(request, 'bookings/booking_cancel_confirm.html', {'booking': booking})


class RecommendationView(LoginRequiredMixin, FormView):
    """场地推荐视图"""
    form_class = RecommendationForm
    template_name = 'bookings/recommendation_form.html'
    
    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        
        required_equipment_ids = list(
            cleaned_data.get('required_equipments', []).values_list('id', flat=True)
        )
        
        request = RecommendationRequest(
            start_time=cleaned_data['start_time'],
            end_time=cleaned_data['end_time'],
            participant_count=cleaned_data['participant_count'],
            required_equipment_ids=required_equipment_ids,
            preferred_building_id=cleaned_data.get('preferred_building').id if cleaned_data.get('preferred_building') else None,
            user_id=self.request.user.id
        )
        
        recommendations, alternative = RecommendationService.recommend(request)
        
        return render(self.request, 'bookings/recommendation_result.html', {
            'recommendations': recommendations,
            'alternative': alternative,
            'request_data': {
                'start_time': cleaned_data['start_time'],
                'end_time': cleaned_data['end_time'],
                'participant_count': cleaned_data['participant_count'],
                'required_equipments': cleaned_data.get('required_equipments', []),
                'preferred_building': cleaned_data.get('preferred_building')
            }
        })


class ApprovalListView(LoginRequiredMixin, ListView):
    """管理员审批列表"""
    model = Booking
    template_name = 'bookings/approval_list.html'
    context_object_name = 'bookings'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, '需要管理员权限')
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Booking.objects.filter(status=Booking.Status.PENDING)
        queryset = queryset.select_related('venue', 'venue__building', 'user')
        
        venue_id = self.request.GET.get('venue')
        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)
        
        return queryset.order_by('start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = Room.objects.filter(status=Room.Status.AVAILABLE)
        return context


@login_required
def approve_booking(request, pk):
    """审批通过"""
    if not request.user.is_admin:
        messages.error(request, '需要管理员权限')
        return redirect('users:home')
    
    booking = get_object_or_404(Booking, pk=pk)
    
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            try:
                result = ApprovalService.approve_booking(
                    booking=booking,
                    approver=request.user,
                    comment=form.cleaned_data.get('comment', '')
                )
                messages.success(request, f'预约 {booking.booking_no} 已通过审批')
                return redirect('bookings:approval_list')
            except Exception as e:
                messages.error(request, f'审批失败：{str(e)}')
    else:
        form = ApprovalForm()
    
    return render(request, 'bookings/approval_form.html', {
        'booking': booking,
        'form': form,
        'action': 'approve'
    })


@login_required
def reject_booking(request, pk):
    """审批拒绝"""
    if not request.user.is_admin:
        messages.error(request, '需要管理员权限')
        return redirect('users:home')
    
    booking = get_object_or_404(Booking, pk=pk)
    
    if request.method == 'POST':
        form = RejectionForm(request.POST)
        if form.is_valid():
            try:
                result = ApprovalService.reject_booking(
                    booking=booking,
                    approver=request.user,
                    reason=form.cleaned_data['reason']
                )
                messages.success(request, f'预约 {booking.booking_no} 已被拒绝')
                return redirect('bookings:approval_list')
            except Exception as e:
                messages.error(request, f'拒绝失败：{str(e)}')
    else:
        form = RejectionForm()
    
    return render(request, 'bookings/approval_form.html', {
        'booking': booking,
        'form': form,
        'action': 'reject'
    })


@login_required
def cancel_booking_view(request, pk):
    """取消预约"""
    booking = get_object_or_404(Booking, pk=pk)
    
    if request.method == 'POST':
        form = CancelForm(request.POST)
        if form.is_valid():
            try:
                if request.user.is_admin:
                    result = ApprovalService.cancel_booking_by_admin(
                        booking=booking,
                        admin=request.user,
                        reason=form.cleaned_data.get('reason', '管理员取消')
                    )
                else:
                    result = ApprovalService.cancel_booking_by_user(
                        booking=booking,
                        user=request.user,
                        reason=form.cleaned_data.get('reason', '')
                    )
                messages.success(request, '预约已取消')
                return redirect('bookings:booking_list')
            except Exception as e:
                messages.error(request, f'取消失败：{str(e)}')
    else:
        form = CancelForm()
    
    return render(request, 'bookings/cancel_form.html', {
        'booking': booking,
        'form': form
    })


class CalendarView(LoginRequiredMixin, TemplateView):
    """日历视图"""
    template_name = 'bookings/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        venue_id = self.request.GET.get('venue')
        if venue_id:
            context['venue'] = get_object_or_404(Room, pk=venue_id)
        
        context['venues'] = Room.objects.filter(status=Room.Status.AVAILABLE)
        return context


@login_required
def calendar_events(request):
    """日历事件数据（AJAX）"""
    import json
    from datetime import datetime
    
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    venue_id = request.GET.get('venue')
    
    queryset = Booking.objects.all()
    
    if venue_id:
        queryset = queryset.filter(venue_id=venue_id)
    
    if start_str:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        queryset = queryset.filter(end_time__gte=start_date)
    
    if end_str:
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        queryset = queryset.filter(start_time__lte=end_date)
    
    events = []
    for booking in queryset:
        events.append({
            'id': booking.id,
            'title': f'{booking.title} ({booking.get_status_display()})',
            'start': booking.start_time.isoformat(),
            'end': booking.end_time.isoformat(),
            'color': booking.get_status_color(),
            'url': f'/bookings/{booking.id}/',
            'extendedProps': {
                'status': booking.status,
                'status_display': booking.get_status_display(),
                'venue': booking.venue.name,
                'user': booking.user.username
            }
        })
    
    return JsonResponse(events, safe=False)


class StatisticsView(LoginRequiredMixin, TemplateView):
    """统计页面"""
    template_name = 'bookings/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        from datetime import datetime
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        context['start_date'] = start_date or (timezone.now().date() - timezone.timedelta(days=30))
        context['end_date'] = end_date or timezone.now().date()
        
        return context


@login_required
def api_venue_utilization(request):
    """场地利用率API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    venue_id = request.GET.get('venue_id')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_venue_utilization(
        venue_id=venue_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_booking_trend(request):
    """预约趋势API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    granularity = request.GET.get('granularity', 'day')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_booking_trend(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_booking_type_statistics(request):
    """预约类型统计API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_booking_type_statistics(
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_status_distribution(request):
    """状态分布API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_status_distribution(
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_popular_venues(request):
    """热门场地API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    limit = int(request.GET.get('limit', 10))
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_popular_venues(
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_time_distribution(request):
    """时间段分布API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_time_distribution(
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)


@login_required
def api_building_statistics(request):
    """楼宇统计API"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    data = StatisticsService.get_building_statistics(
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse(data, safe=False)