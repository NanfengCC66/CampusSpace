from django import forms
from django.utils import timezone
from .models import Booking
from apps.venues.models import Equipment, Building


class ApprovalForm(forms.Form):
    comment = forms.CharField(
        label='审批意见',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': '请输入审批意见（可选）'
        })
    )


class RejectionForm(forms.Form):
    reason = forms.CharField(
        label='拒绝原因',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': '请输入拒绝原因（必填）'
        })
    )


class CancelForm(forms.Form):
    reason = forms.CharField(
        label='取消原因',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '2',
            'placeholder': '请输入取消原因（可选）'
        })
    )


class RecommendationForm(forms.Form):
    start_time = forms.DateTimeField(
        label='开始时间',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    end_time = forms.DateTimeField(
        label='结束时间',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    participant_count = forms.IntegerField(
        label='参与人数',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )
    
    required_equipments = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='所需设备'
    )
    
    preferred_building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='偏好建筑'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError('开始时间必须早于结束时间')
            
            if start_time <= timezone.now():
                raise forms.ValidationError('开始时间必须在未来')
            
            duration = (end_time - start_time).total_seconds() / 60
            if duration < 30:
                raise forms.ValidationError('预约时长不能少于30分钟')
            if duration > 8 * 60:
                raise forms.ValidationError('预约时长不能超过8小时')
        
        return cleaned_data


class BookingCreateForm(forms.ModelForm):
    """创建预约表单"""
    
    class Meta:
        model = Booking
        fields = ['title', 'booking_type', 'start_time', 'end_time',
                  'participant_count',
                  'contact_name', 'contact_phone', 'remark']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入使用目的'
            }),
            'booking_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'participant_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
        }
        
        labels = {
            'title': '使用目的',
            'booking_type': '预约用途',
            'start_time': '开始时间',
            'end_time': '结束时间',
            'participant_count': '参与人数',
            'contact_name': '联系人',
            'contact_phone': '联系电话',
            'remark': '备注',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            # 检查开始时间是否早于结束时间
            if start_time >= end_time:
                raise forms.ValidationError('开始时间必须早于结束时间')
            
            # 检查开始时间是否在未来
            if start_time <= timezone.now():
                raise forms.ValidationError('开始时间必须在未来')
            
            # 检查预约时长
            duration = (end_time - start_time).total_seconds() / 60
            if duration < 30:
                raise forms.ValidationError('预约时长不能少于30分钟')
            if duration > 8 * 60:
                raise forms.ValidationError('预约时长不能超过8小时')
        
        return cleaned_data
    
    def clean_participant_count(self):
        participant_count = self.cleaned_data.get('participant_count')
        if participant_count and participant_count < 1:
            raise forms.ValidationError('参与人数至少为1人')
        return participant_count