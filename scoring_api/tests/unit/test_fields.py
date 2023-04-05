import datetime
import unittest

from scoring_api import api


class CharFieldTest(unittest.TestCase):
    """Tests for field descriptors. How validation works"""
    def setUp(self):
        class ClassWithFields:
            nf_chf = api.CharField(required=False, nullable=True)
            nnf_chf = api.CharField(required=False, nullable=False)
            af = api.ArgumentsField(required=True, nullable=True)
            ef = api.EmailField(required=True, nullable=True)
            pf = api.PhoneField(required=True, nullable=True)
            df = api.DateField(required=True, nullable=True)
            bdf = api.BirthDayField(required=True, nullable=True)
            gf = api.GenderField(required=True, nullable=True)
            cif = api.ClientIDsField(required=True, nullable=True)
        self.instance_with_fields = ClassWithFields()

    def test_validate_nullable(self):  # this also tests descriptors and BaseField class
        setattr(self.instance_with_fields, 'nf_chf', None)
        self.assertEqual(None, getattr(self.instance_with_fields, 'nf_chf'))

        setattr(self.instance_with_fields, 'nf_chf', 'something nf')
        self.assertEqual('something nf', getattr(self.instance_with_fields, 'nf_chf'))

        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'nnf_chf', None)

        setattr(self.instance_with_fields, 'nnf_chf', 'something nnf')
        self.assertEqual('something nnf', getattr(self.instance_with_fields, 'nnf_chf'))

    def test_validate_char_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'nf_chf', 3)

    def test_validate_arguments_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'af', 3)  # dict expected
        setattr(self.instance_with_fields, 'af', {})
        self.assertEqual({}, getattr(self.instance_with_fields, 'af'))

    def test_validate_email_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'ef', 'ds @motw.net')  # invalid email
        setattr(self.instance_with_fields, 'ef', 'ds@motw.net')
        self.assertEqual('ds@motw.net', getattr(self.instance_with_fields, 'ef'))

    def test_validate_phone_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', 'not a phone number')
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', '82345678900')  # not starting with 1
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', '1123456789')  # not 11
        setattr(self.instance_with_fields, 'pf', '11234567890')  # accepts strings
        self.assertEqual('11234567890', getattr(self.instance_with_fields, 'pf'))
        setattr(self.instance_with_fields, 'pf', 11234567890)  # accepts numbers
        self.assertEqual(11234567890, getattr(self.instance_with_fields, 'pf'))

    def test_validate_date_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'df', '11.11.11')  # not dd.mm.yyyy format
        setattr(self.instance_with_fields, 'df', '11.11.2011')
        self.assertEqual(datetime.date(2011, 11, 11), getattr(self.instance_with_fields, 'df'))

    def test_validate_birthdate_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'bdf', '01.01.1900')  # age > 70
        setattr(self.instance_with_fields, 'bdf', '11.11.2011')
        self.assertEqual(datetime.date(2011, 11, 11), getattr(self.instance_with_fields, 'bdf'))

    def test_validate_gender_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'gf', '2')  # NaN
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'gf', 11)  # not in the list
        setattr(self.instance_with_fields, 'gf', 2)
        self.assertEqual(2, getattr(self.instance_with_fields, 'gf'))

    def test_validate_client_ids_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'cif', '[1, 2, 3]')  # not a list
        setattr(self.instance_with_fields, 'cif', [1, 2, 3])
        self.assertEqual([1, 2, 3], getattr(self.instance_with_fields, 'cif'))

if __name__ == "__main__":
    unittest.main()
