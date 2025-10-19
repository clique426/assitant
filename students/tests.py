
from django.test import TestCase
from django.contrib.auth.models import User
from .models import StudentProfile, ScoreItem

class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.student = StudentProfile.objects.create(
            user=self.user,
            full_name='Test Student',
            student_id='123456'
        )

    def test_student_creation(self):
        self.assertEqual(self.student.full_name, 'Test Student')
        self.assertEqual(str(self.student), 'Test Student（123456）')