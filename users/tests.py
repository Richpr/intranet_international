from django.test import TestCase
from django.contrib.auth import get_user_model
from .forms import ProfileUpdateForm

User = get_user_model()

class UserFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123'
        )
        self.form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
        }

    def test_phone_number_validation_valid_international_number(self):
        """Test that a valid international number is accepted."""
        data = self.form_data.copy()
        data['phone_number'] = '+33612345678'  # Valid French number
        form = ProfileUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid(), form.errors.as_data())
        self.assertEqual(form.cleaned_data['phone_number'], '+33612345678')

    def test_phone_number_validation_invalid_number_raises_error(self):
        """Test that an invalid number raises a validation error."""
        data = self.form_data.copy()
        data['phone_number'] = '+123'  # Invalid number
        form = ProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)
        self.assertEqual(form.errors['phone_number'][0], "Le numéro de téléphone n'est pas valide.")

    def test_phone_number_validation_missing_country_code_raises_error(self):
        """Test that a number without a country code raises a validation error."""
        data = self.form_data.copy()
        data['phone_number'] = '0612345678'  # Number without '+'
        form = ProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)
        self.assertEqual(form.errors['phone_number'][0], "Le numéro de téléphone doit commencer par l'indicatif du pays (ex: +229 pour le Bénin).")

    def test_phone_number_validation_empty_number_is_allowed(self):
        """Test that an empty phone number is allowed."""
        data = self.form_data.copy()
        data['phone_number'] = ''
        form = ProfileUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid(), form.errors.as_data())
        self.assertIsNone(form.cleaned_data['phone_number'])

    def test_phone_number_validation_just_plus_is_invalid(self):
        """Test that a single '+' is not a valid number."""
        data = self.form_data.copy()
        data['phone_number'] = '+'
        form = ProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)
        self.assertEqual(form.errors['phone_number'][0], "Format du numéro de téléphone invalide.")