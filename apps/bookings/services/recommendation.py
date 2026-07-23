from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from apps.venues.models import Room, Building
from apps.bookings.models import Booking
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance
import math


@dataclass
class RecommendationRequest:
    start_time: datetime
    end_time: datetime
    participant_count: int
    required_equipment_ids: List[int]
    preferred_building_id: Optional[int] = None
    user_id: Optional[int] = None


@dataclass
class ScoreDetail:
    capacity_score: float = 0.0
    equipment_score: float = 0.0
    building_score: float = 0.0
    continuity_score: float = 0.0
    energy_score: float = 0.0
    total_score: float = 0.0
    
    reasons: List[str] = field(default_factory=list)
    deductions: List[str] = field(default_factory=list)


@dataclass
class RecommendationResult:
    room: Room
    score_detail: ScoreDetail
    rank: int = 0
    
    def get_total_score(self) -> float:
        return self.score_detail.total_score


@dataclass
class AlternativeSuggestion:
    suggestion_type: str
    message: str
    available_slots: List[Dict] = field(default_factory=list)
    alternative_rooms: List[Room] = field(default_factory=list)


class RecommendationService:
    CAPACITY_WEIGHT = 35
    EQUIPMENT_WEIGHT = 25
    BUILDING_WEIGHT = 15
    CONTINUITY_WEIGHT = 15
    ENERGY_WEIGHT = 10
    
    MAX_RESULTS = 3
    
    ENERGY_SAVING_HOURS = {
        'start': 8,
        'end': 18
    }
    
    @classmethod
    def recommend(cls, request: RecommendationRequest) -> Tuple[List[RecommendationResult], Optional[AlternativeSuggestion]]:
        candidate_rooms = cls._filter_candidates(request)
        
        if not candidate_rooms:
            alternative = cls._generate_alternatives(request)
            return [], alternative
        
        scored_results = []
        for room in candidate_rooms:
            score_detail = cls._calculate_score(room, request)
            scored_results.append(RecommendationResult(
                room=room,
                score_detail=score_detail
            ))
        
        scored_results.sort(key=lambda x: x.get_total_score(), reverse=True)
        
        for idx, result in enumerate(scored_results[:cls.MAX_RESULTS]):
            result.rank = idx + 1
        
        return scored_results[:cls.MAX_RESULTS], None
    
    @classmethod
    def _filter_candidates(cls, request: RecommendationRequest) -> List[Room]:
        rooms = Room.objects.filter(
            status=Room.Status.AVAILABLE,
            capacity__gte=request.participant_count
        ).select_related('building')
        
        candidate_rooms = []
        for room in rooms:
            if cls._check_time_availability(room, request.start_time, request.end_time):
                candidate_rooms.append(room)
        
        return candidate_rooms
    
    @classmethod
    def _check_time_availability(cls, room: Room, start_time: datetime, end_time: datetime) -> bool:
        if Booking.objects.filter(
            venue=room,
            status__in=['approved', 'pending'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists():
            return False
        
        # TODO: 实现固定课表冲突检测
        # Schedule模型使用day_of_week、period、start_week、end_week字段
        # 需要将预约时间转换为周次、星期、节次进行判断
        
        if Maintenance.objects.filter(
            venue=room,
            status__in=['approved', 'ongoing'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists():
            return False
        
        return True
    
    @classmethod
    def _calculate_score(cls, room: Room, request: RecommendationRequest) -> ScoreDetail:
        detail = ScoreDetail()
        
        detail.capacity_score = cls._calculate_capacity_score(room, request, detail)
        detail.equipment_score = cls._calculate_equipment_score(room, request, detail)
        detail.building_score = cls._calculate_building_score(room, request, detail)
        detail.continuity_score = cls._calculate_continuity_score(room, request, detail)
        detail.energy_score = cls._calculate_energy_score(room, request, detail)
        
        detail.total_score = (
            detail.capacity_score +
            detail.equipment_score +
            detail.building_score +
            detail.continuity_score +
            detail.energy_score
        )
        
        return detail
    
    @classmethod
    def _calculate_capacity_score(cls, room: Room, request: RecommendationRequest, detail: ScoreDetail) -> float:
        capacity = room.capacity
        needed = request.participant_count
        
        if capacity == needed:
            detail.reasons.append(f"容量完美匹配（{needed}人）")
            return cls.CAPACITY_WEIGHT
        
        ratio = needed / capacity
        score = cls.CAPACITY_WEIGHT * ratio
        
        waste_ratio = (capacity - needed) / capacity
        if waste_ratio > 0.5:
            detail.deductions.append(f"容量浪费较大（浪费{int(waste_ratio * 100)}%）")
            score *= 0.7
        elif waste_ratio > 0.3:
            detail.deductions.append(f"容量略大（浪费{int(waste_ratio * 100)}%）")
            score *= 0.9
        
        return round(score, 2)
    
    @classmethod
    def _calculate_equipment_score(cls, room: Room, request: RecommendationRequest, detail: ScoreDetail) -> float:
        if not request.required_equipment_ids:
            detail.reasons.append("无特殊设备需求")
            return cls.EQUIPMENT_WEIGHT
        
        room_equipment_ids = set(room.room_equipments.values_list('equipment_id', flat=True))
        required_ids = set(request.required_equipment_ids)
        
        matched = room_equipment_ids & required_ids
        missing = required_ids - room_equipment_ids
        
        if not missing:
            detail.reasons.append("设备完全满足需求")
            return cls.EQUIPMENT_WEIGHT
        
        match_ratio = len(matched) / len(required_ids)
        score = cls.EQUIPMENT_WEIGHT * match_ratio
        
        from apps.venues.models import Equipment
        missing_names = Equipment.objects.filter(id__in=missing).values_list('name', flat=True)
        detail.deductions.append(f"缺少设备：{', '.join(missing_names)}（需自备）")
        
        return round(score, 2)
    
    @classmethod
    def _calculate_building_score(cls, room: Room, request: RecommendationRequest, detail: ScoreDetail) -> float:
        if not request.preferred_building_id:
            detail.reasons.append("无建筑偏好")
            return cls.BUILDING_WEIGHT
        
        if room.building_id == request.preferred_building_id:
            detail.reasons.append("符合建筑偏好")
            return cls.BUILDING_WEIGHT
        
        detail.deductions.append("不在偏好建筑内")
        return cls.BUILDING_WEIGHT * 0.5
    
    @classmethod
    def _calculate_continuity_score(cls, room: Room, request: RecommendationRequest, detail: ScoreDetail) -> float:
        before_free = cls._check_time_availability(
            room,
            request.start_time - timedelta(hours=1),
            request.start_time
        )
        
        after_free = cls._check_time_availability(
            room,
            request.end_time,
            request.end_time + timedelta(hours=1)
        )
        
        if before_free and after_free:
            detail.reasons.append("前后时间段空闲，便于灵活调整")
            return cls.CONTINUITY_WEIGHT
        elif before_free or after_free:
            detail.reasons.append("一侧时间段空闲")
            return cls.CONTINUITY_WEIGHT * 0.7
        else:
            detail.deductions.append("前后时间段已被占用")
            return cls.CONTINUITY_WEIGHT * 0.3
    
    @classmethod
    def _calculate_energy_score(cls, room: Room, request: RecommendationRequest, detail: ScoreDetail) -> float:
        start_hour = request.start_time.hour
        end_hour = request.end_time.hour
        
        energy_start = cls.ENERGY_SAVING_HOURS['start']
        energy_end = cls.ENERGY_SAVING_HOURS['end']
        
        if start_hour >= energy_start and end_hour <= energy_end:
            detail.reasons.append("在节能时间段内（8:00-18:00）")
            return cls.ENERGY_WEIGHT
        
        if start_hour < energy_start:
            detail.deductions.append(f"开始时间过早（早于{energy_start}:00）")
        if end_hour > energy_end:
            detail.deductions.append(f"结束时间过晚（晚于{energy_end}:00）")
        
        return cls.ENERGY_WEIGHT * 0.5
    
    @classmethod
    def _generate_alternatives(cls, request: RecommendationRequest) -> AlternativeSuggestion:
        nearby_slots = cls._find_nearby_available_slots(request)
        
        if nearby_slots:
            return AlternativeSuggestion(
                suggestion_type='time_alternative',
                message='未找到符合条件的场地，但发现以下时间段有空闲场地：',
                available_slots=nearby_slots
            )
        
        alternative_rooms = cls._find_alternative_rooms(request)
        
        if alternative_rooms:
            return AlternativeSuggestion(
                suggestion_type='room_alternative',
                message='未找到完全符合条件的场地，以下场地可能满足部分需求：',
                alternative_rooms=alternative_rooms
            )
        
        return AlternativeSuggestion(
            suggestion_type='no_alternative',
            message='当前时间段所有场地均不可用，建议调整预约时间或减少参与人数'
        )
    
    @classmethod
    def _find_nearby_available_slots(cls, request: RecommendationRequest) -> List[Dict]:
        slots = []
        
        for delta_days in range(0, 8):
            for delta_hours in [-2, -1, 1, 2]:
                new_start = request.start_time + timedelta(days=delta_days, hours=delta_hours)
                new_end = request.end_time + timedelta(days=delta_days, hours=delta_hours)
                
                if new_start <= timezone.now():
                    continue
                
                available_rooms = Room.objects.filter(
                    status=Room.Status.AVAILABLE,
                    capacity__gte=request.participant_count
                )
                
                count = 0
                for room in available_rooms:
                    if cls._check_time_availability(room, new_start, new_end):
                        count += 1
                
                if count > 0:
                    slots.append({
                        'start_time': new_start,
                        'end_time': new_end,
                        'available_count': count
                    })
        
        return slots[:5]
    
    @classmethod
    def _find_alternative_rooms(cls, request: RecommendationRequest) -> List[Room]:
        rooms = Room.objects.filter(
            status=Room.Status.AVAILABLE,
            capacity__gte=request.participant_count
        ).select_related('building')
        
        available_rooms = []
        for room in rooms:
            if cls._check_time_availability(room, request.start_time, request.end_time):
                available_rooms.append(room)
        
        return available_rooms[:5]