import logging
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDay, TruncYear
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
import datetime

from studentsdb.models import Student
from trainersdb.models import Trainer
from rbac.models import OnboardRequest
from batchdb.models import Batch

User = get_user_model()
logger = logging.getLogger(__name__)

class DashboardService:
    """
    Service layer for Dashboard Analytics.
    Handles data scoping based on User Role (Admin, Trainer, Student).
    Implements Caching for performance.
    """
    
    CACHE_TTL_STATS = 60 * 5  # 5 Minutes
    CACHE_TTL_CHARTS = 60 * 15 # 15 Minutes

    def __init__(self, user, active_role_code):
        self.user = user
        self.role = active_role_code
        self.is_admin = active_role_code == 'ADMIN' or user.is_superuser
        self.is_trainer = active_role_code == 'TRAINER'
        self.is_student = active_role_code == 'STUDENT'

    def get_hero_stats(self):
        """
        Returns high-level stats for the dashboard hero cards.
        Scoped by role.
        """
        cache_key = f"dash_stats_{self.user.id}_{self.role}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        stats = []

        if self.is_admin:
            # ADMIN: Global View
            total_students = Student.objects.count()
            active_students = Student.objects.filter(course_status='IP').count()
            total_trainers = Trainer.objects.count()
            active_batches = Batch.objects.filter(batch_status='IP').count()
            pending_requests = OnboardRequest.objects.filter(status='PENDING_APPROVAL').count()

            stats = [
                {"label": "Total Students", "value": total_students, "trend": "+5%", "color": "blue"},
                {"label": "Active Learners", "value": active_students, "trend": "+12%", "color": "green"},
                {"label": "Active Batches", "value": active_batches, "trend": "", "color": "purple"},
                {"label": "Pending Requests", "value": pending_requests, "trend": "Urgent", "color": "red"},
            ]

        elif self.is_trainer:
            # TRAINER: My Students
            try:
                trainer_profile = getattr(self.user, 'trainer_profile_link', None)
                if trainer_profile:
                    my_students = Student.objects.filter(trainer=trainer_profile)
                    total_my_students = my_students.count()
                    active_my_students = my_students.filter(course_status='IP').count()
                    
                    my_batches_count = Batch.objects.filter(trainer=trainer_profile, batch_status='IP').count()
                    
                    stats = [
                        {"label": "My Students", "value": total_my_students, "trend": "", "color": "blue"},
                        {"label": "Active Learners", "value": active_my_students, "trend": "", "color": "green"},
                        {"label": "My Batches", "value": my_batches_count, "trend": "Active", "color": "purple"},
                    ]
                else:
                    stats = [{"label": "Profile Error", "value": "No Trainer Profile", "trend": "", "color": "red"}]
            except Exception as e:
                logger.error(f"Error fetching trainer stats: {e}")
                stats = [{"label": "Error", "value": "System Error", "trend": "", "color": "red"}]

        elif self.is_student:
            # STUDENT: My Progress
            try:
                student_profile = getattr(self.user, 'student_profile', None)
                if student_profile:
                    course_status = student_profile.get_course_status_display()
                    # Placeholder for attendance/grade
                    attendance = "N/A" 
                    
                    stats = [
                        {"label": "Course Status", "value": course_status, "trend": "", "color": "blue"},
                        {"label": "Attendance", "value": attendance, "trend": "Good", "color": "green"},
                    ]
                else:
                    stats = [{"label": "Profile Error", "value": "No Student Profile", "trend": "", "color": "red"}]
            except Exception as e:
                logger.error(f"Error fetching student stats: {e}")
                stats = [{"label": "Error", "value": "System Error", "trend": "", "color": "red"}]

        cache.set(cache_key, stats, self.CACHE_TTL_STATS)
        return stats

    def get_growth_trend(self, period='6m'):
        """
        Returns student enrollment growth over time.
        Supports: '30d' (Day), '6m' (Month), '1y' (Month), 'all' (Year)
        """
        cache_key = f"dash_growth_{self.user.id}_{self.role}_{period}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        # 1. Determine Truncation, Date Range, and Format
        now = timezone.now()
        trunc_func = TruncMonth
        date_format = "%b" # Jan
        
        start_date = None
        
        # Helper to generate range labels
        labels = []
        
        if period == '30d':
            # Day-wise
            trunc_func = TruncDay
            date_format = "%d %b" # 01 Oct
            start_date = now - datetime.timedelta(days=30)
            
            # Generate last 30 days labels
            for i in range(29, -1, -1):
                d = now - datetime.timedelta(days=i)
                labels.append(d.strftime(date_format))
                
        elif period == '6m':
            # Month-wise
            trunc_func = TruncMonth
            date_format = "%b" # Jan
            start_date = now - datetime.timedelta(days=180) # Approx 6 months
            
            # Generate last 6 months labels
            # Go back to 1st of current month to align
            curr_month = now.replace(day=1)
            for i in range(5, -1, -1):
                # Simple month subtraction
                # (Not perfect for edge cases but good for charts)
                # Better: use relativedelta, but sticking to stdlib
                # Calculate approximate date for label
                d = curr_month - datetime.timedelta(days=i*30)
                labels.append(d.strftime(date_format))

        elif period == '1y':
            # Month-wise
            trunc_func = TruncMonth
            date_format = "%b" # Jan
            start_date = now - datetime.timedelta(days=365)
            
            curr_month = now.replace(day=1)
            for i in range(11, -1, -1):
                d = curr_month - datetime.timedelta(days=i*30)
                labels.append(d.strftime(date_format))

        elif period == 'all':
            # Year-wise
            trunc_func = TruncYear
            date_format = "%Y" # 2024
            # No start date filter (All time)
            start_date = None 
            
            # For 'all', we can't pre-generate labels easily without knowing min date.
            # So we will let the DB drive the labels or query min date first.
            # Strategy: Query DB for min year, then generate range to Now.
            pass

        # 2. Prepare Base QuerySets
        student_qs = Student.objects.all()
        trainer_qs = Trainer.objects.all() # Or Active Learners based on requirement

        if self.is_trainer:
             if hasattr(self.user, 'trainer_profile_link'):
                student_qs = student_qs.filter(trainer=self.user.trainer_profile_link)
                # For Trainer, second series is "My Batches"
                trainer_qs = Batch.objects.filter(trainer=self.user.trainer_profile_link)
             else:
                student_qs = student_qs.none()
                trainer_qs = Batch.objects.none()
        elif self.is_student:
             return {} # Not applicable

        # 3. Helper to fetch grouped data
        def get_grouped_data(queryset, date_field):
            q = queryset
            if start_date:
                q = q.filter(**{f"{date_field}__gte": start_date})
            
            data = (
                q.annotate(period_label=trunc_func(date_field))
                .values('period_label')
                .annotate(count=Count('id'))
                .order_by('period_label')
            )
            
            # Convert to dict: { "Label": Count }
            result = {}
            for entry in data:
                if entry['period_label']:
                    lbl = entry['period_label'].strftime(date_format)
                    result[lbl] = entry['count']
            return result

        # Execute Queries
        student_counts = get_grouped_data(student_qs, 'enrollment_date')
        
        second_field = 'date_of_joining'
        if self.is_trainer:
            second_field = 'start_date' # Batch start date
        
        second_counts = get_grouped_data(trainer_qs, second_field)

        # 4. Handle 'all' period labels dynamically if needed
        if period == 'all':
            # Find all unique labels from both datasets and sort them
            all_keys = set(student_counts.keys()) | set(second_counts.keys())
            if not all_keys:
                labels = [now.strftime(date_format)] # Default to current year if empty
            else:
                labels = sorted(list(all_keys))

        # 5. Construct Final Data Arrays (Zero Filling)
        student_data = []
        second_data = []

        for lbl in labels:
            student_data.append(student_counts.get(lbl, 0))
            second_data.append(second_counts.get(lbl, 0))

        # 6. Build Response
        response_data = {
            "xAxis": labels,
            "series": [
                {
                    "name": "Total Students",
                    "data": student_data
                },
                {
                    "name": "Total Trainers" if not self.is_trainer else "My Batches",
                    "data": second_data
                }
            ]
        }

        cache.set(cache_key, response_data, self.CACHE_TTL_CHARTS)
        return response_data

    def get_distribution_data(self):
        """
        Returns distribution of users over time (Active vs Inactive).
        Expected format:
        {
          "categories": ["Jan", "Feb", ...],
          "active_data": [10, 20, ...],
          "inactive_data": [5, 2, ...]
        }
        """
        cache_key = f"dash_dist_{self.user.id}_{self.role}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        response_data = {
            "categories": [],
            "active_data": [],
            "inactive_data": []
        }
        
        qs = Student.objects.all()

        if self.is_trainer:
             if hasattr(self.user, 'trainer_profile_link'):
                qs = qs.filter(trainer=self.user.trainer_profile_link)
             else:
                qs = qs.none()
        elif self.is_student:
             return {}

        # Logic: Group by Month.
        # Active: IP, P, C, YTS
        # Inactive: R, D, H
        
        active_statuses = ['IP', 'P', 'C', 'YTS']
        inactive_statuses = ['R', 'D', 'H']
        
        months = 6
        start_date = timezone.now() - timezone.timedelta(days=months*30)
        
        raw_data = (
            qs.filter(enrollment_date__gte=start_date)
            .annotate(month=TruncMonth('enrollment_date'))
            .values('month', 'course_status')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # Process into Dict: { "Jan": { "active": 10, "inactive": 5 } }
        processed = {}
        for entry in raw_data:
            if not entry['month']: continue
            month_label = entry['month'].strftime("%b")
            
            if month_label not in processed:
                processed[month_label] = {"active": 0, "inactive": 0}
            
            if entry['course_status'] in active_statuses:
                processed[month_label]["active"] += entry['count']
            else:
                processed[month_label]["inactive"] += entry['count']
                
        # Fill Arrays
        import datetime
        current = timezone.now()
        for i in range(months - 1, -1, -1):
            target_date = current - datetime.timedelta(days=i*30)
            month_label = target_date.strftime("%b")
            
            response_data["categories"].append(month_label)
            
            data = processed.get(month_label, {"active": 0, "inactive": 0})
            response_data["active_data"].append(data["active"])
            response_data["inactive_data"].append(data["inactive"])

        cache.set(cache_key, response_data, self.CACHE_TTL_CHARTS)
        return response_data

    def get_schedule_today(self):
        """
        Returns today's schedule based on Active Batches.
        """
        cache_key = f"dash_schedule_{self.user.id}_{self.role}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        today_name = timezone.now().strftime('%A') # e.g., 'Monday'
        schedule = []
        
        # 1. Base Query: Active Batches
        qs = Batch.objects.filter(batch_status='IP')
        
        # 2. Scope Query
        if self.is_admin:
            pass # All active batches
        elif self.is_trainer:
            if hasattr(self.user, 'trainer_profile_link'):
                qs = qs.filter(trainer=self.user.trainer_profile_link)
            else:
                qs = qs.none()
        elif self.is_student:
            if hasattr(self.user, 'student_profile'):
                # ManyToMany relationship
                qs = qs.filter(students=self.user.student_profile)
            else:
                qs = qs.none()
        
        # 3. Filter by Day (Memory filter because JSONField query varies by DB)
        # We fetch all active scoped batches and filter in python for robustness across DBs (SQLite/Postgres)
        # unless we are sure about JSON operator support.
        # For small batch counts, python filtering is fine.
        
        active_batches = list(qs)
        for batch in active_batches:
            # Check if today is in batch.days (Case insensitive check)
            if batch.days and any(day.lower() == today_name.lower() for day in batch.days):
                schedule.append({
                    "id": batch.id,
                    "title": f"{batch.batch_id} - {batch.course.name if batch.course else 'Course'}",
                    "time": batch.get_slottime,
                    "trainer": batch.trainer.name if batch.trainer else "TBD",
                    "type": batch.batch_type
                })
        
        # Sort by time? String sort for now.
        schedule.sort(key=lambda x: x['time'])
        
        cache.set(cache_key, schedule, 60 * 60) # Cache for 1 hour
        return schedule
