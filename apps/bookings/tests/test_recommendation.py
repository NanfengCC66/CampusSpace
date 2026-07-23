from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.venues.models import Building, Room, Equipment, RoomEquipment
from apps.users.models import User
from apps.bookings.models import Booking
from apps.bookings.services import RecommendationService, RecommendationRequest


class RecommendationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student'
        )
        
        self.building1 = Building.objects.create(
            name='教学楼A',
            total_floors=5,
            description='主教学楼'
        )
        
        self.building2 = Building.objects.create(
            name='教学楼B',
            total_floors=3,
            description='副教学楼'
        )
        
        self.projector = Equipment.objects.create(
            name='投影仪',
            code='PROJECTOR',
            description='高清投影仪'
        )
        
        self.computer = Equipment.objects.create(
            name='电脑',
            code='COMPUTER',
            description='教学电脑'
        )
        
        self.microphone = Equipment.objects.create(
            name='麦克风',
            code='MIC',
            description='无线麦克风'
        )
        
        self.room1 = Room.objects.create(
            name='教室A101',
            room_number='A101',
            building=self.building1,
            capacity=50,
            venue_type='classroom',
            status=Room.Status.AVAILABLE
        )
        RoomEquipment.objects.create(room=self.room1, equipment=self.projector)
        RoomEquipment.objects.create(room=self.room1, equipment=self.computer)
        
        self.room2 = Room.objects.create(
            name='教室A102',
            room_number='A102',
            building=self.building1,
            capacity=30,
            venue_type='classroom',
            status=Room.Status.AVAILABLE
        )
        RoomEquipment.objects.create(room=self.room2, equipment=self.projector)
        
        self.room3 = Room.objects.create(
            name='教室B201',
            room_number='B201',
            building=self.building2,
            capacity=100,
            venue_type='classroom',
            status=Room.Status.AVAILABLE
        )
        RoomEquipment.objects.create(room=self.room3, equipment=self.projector)
        RoomEquipment.objects.create(room=self.room3, equipment=self.computer)
        RoomEquipment.objects.create(room=self.room3, equipment=self.microphone)
        
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=9)
        self.end_time = self.now + timedelta(days=1, hours=11)
    
    def test_basic_recommendation(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[self.projector.id],
            preferred_building_id=self.building1.id
        )
        
        recommendations, alternative = RecommendationService.recommend(request)
        
        self.assertEqual(len(recommendations), 3)
        self.assertIsNone(alternative)
        
        for i in range(len(recommendations) - 1):
            self.assertGreaterEqual(
                recommendations[i].get_total_score(),
                recommendations[i + 1].get_total_score()
            )
        
        for i, rec in enumerate(recommendations):
            self.assertEqual(rec.rank, i + 1)
    
    def test_capacity_matching_score(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=50,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        room1_rec = next((r for r in recommendations if r.room == self.room1), None)
        self.assertIsNotNone(room1_rec)
        
        self.assertEqual(room1_rec.score_detail.capacity_score, 35)
        self.assertIn('容量完美匹配', room1_rec.score_detail.reasons[0])
    
    def test_equipment_matching_score(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[self.projector.id, self.computer.id],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        room1_rec = next((r for r in recommendations if r.room == self.room1), None)
        self.assertIsNotNone(room1_rec)
        
        self.assertEqual(room1_rec.score_detail.equipment_score, 25)
        self.assertIn('设备完全满足需求', room1_rec.score_detail.reasons)
        
        room2_rec = next((r for r in recommendations if r.room == self.room2), None)
        self.assertIsNotNone(room2_rec)
        
        self.assertEqual(room2_rec.score_detail.equipment_score, 12.5)
        self.assertTrue(any('缺少设备' in d for d in room2_rec.score_detail.deductions))
    
    def test_building_preference_score(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=self.building1.id
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        room1_rec = next((r for r in recommendations if r.room == self.room1), None)
        self.assertIsNotNone(room1_rec)
        self.assertEqual(room1_rec.score_detail.building_score, 15)
        
        room3_rec = next((r for r in recommendations if r.room == self.room3), None)
        self.assertIsNotNone(room3_rec)
        self.assertEqual(room3_rec.score_detail.building_score, 7.5)
    
    def test_no_available_rooms(self):
        Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room1,
            user=self.user,
            title='Test Booking',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=10,
            status='approved'
        )
        
        Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room2,
            user=self.user,
            title='Test Booking 2',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=10,
            status='approved'
        )
        
        Booking.objects.create(
            booking_no='BK20260117000003',
            venue=self.room3,
            user=self.user,
            title='Test Booking 3',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=10,
            status='approved'
        )
        
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, alternative = RecommendationService.recommend(request)
        
        self.assertEqual(len(recommendations), 0)
        self.assertIsNotNone(alternative)
        self.assertIn('未找到', alternative.message)
    
    def test_tie_breaking(self):
        room4 = Room.objects.create(
            name='教室A103',
            room_number='A103',
            building=self.building1,
            capacity=30,
            venue_type='classroom',
            status=Room.Status.AVAILABLE
        )
        RoomEquipment.objects.create(room=room4, equipment=self.projector)
        
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[self.projector.id],
            preferred_building_id=self.building1.id
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        self.assertEqual(len(recommendations), 3)
        
        for i in range(len(recommendations) - 1):
            self.assertGreaterEqual(
                recommendations[i].get_total_score(),
                recommendations[i + 1].get_total_score()
            )
    
    def test_energy_saving_score(self):
        energy_start = self.now + timedelta(days=1, hours=9)
        energy_end = self.now + timedelta(days=1, hours=11)
        
        request = RecommendationRequest(
            start_time=energy_start,
            end_time=energy_end,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        for rec in recommendations:
            self.assertEqual(rec.score_detail.energy_score, 10)
            self.assertTrue(any('节能时间段' in r for r in rec.score_detail.reasons))
        
        non_energy_start = self.now + timedelta(days=1, hours=19)
        non_energy_end = self.now + timedelta(days=1, hours=21)
        
        request2 = RecommendationRequest(
            start_time=non_energy_start,
            end_time=non_energy_end,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations2, _ = RecommendationService.recommend(request2)
        
        for rec in recommendations2:
            self.assertEqual(rec.score_detail.energy_score, 5)
            self.assertTrue(any('结束时间过晚' in d for d in rec.score_detail.deductions))
    
    def test_continuity_score(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        for rec in recommendations:
            self.assertGreater(rec.score_detail.continuity_score, 0)
    
    def test_max_results_limit(self):
        for i in range(4, 8):
            room = Room.objects.create(
                name=f'教室A10{i}',
                room_number=f'A10{i}',
                building=self.building1,
                capacity=30,
                venue_type='classroom',
                status=Room.Status.AVAILABLE
            )
            RoomEquipment.objects.create(room=room, equipment=self.projector)
        
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        self.assertLessEqual(len(recommendations), 3)
    
    def test_inactive_room_excluded(self):
        self.room1.status = Room.Status.DISABLED
        self.room1.save()
        
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        room_ids = [r.room.id for r in recommendations]
        self.assertNotIn(self.room1.id, room_ids)
    
    def test_capacity_filter(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=80,
            required_equipment_ids=[],
            preferred_building_id=None
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        for rec in recommendations:
            self.assertGreaterEqual(rec.room.capacity, 80)
    
    def test_score_breakdown(self):
        request = RecommendationRequest(
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            required_equipment_ids=[self.projector.id],
            preferred_building_id=self.building1.id
        )
        
        recommendations, _ = RecommendationService.recommend(request)
        
        for rec in recommendations:
            expected_total = (
                rec.score_detail.capacity_score +
                rec.score_detail.equipment_score +
                rec.score_detail.building_score +
                rec.score_detail.continuity_score +
                rec.score_detail.energy_score
            )
            self.assertEqual(rec.score_detail.total_score, expected_total)