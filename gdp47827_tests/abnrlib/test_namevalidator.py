#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the classes in the namevalidator.py file
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_namevalidator.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.namevalidator import Validator, ICMName, AlteraName

class TestValidator(unittest.TestCase):
    '''
    Tests the Validator class
    '''

    def test_contains_whitespace_no_whitespace(self):
        '''
        Tests the contains_whitespace method when there is no whitespace
        '''
        self.assertFalse(Validator.contains_whitespace('no_whitespace_in_string'))

    def test_contains_whitespace_space_at_start(self):
        '''
        Tests the contains_whitespace method when there's a space at the start
        '''
        self.assertTrue(Validator.contains_whitespace(' there_was_a_space_over_there'))

    def test_contains_whitespace_space_at_end(self):
        '''
        Tests the contains_whitespace method when there's a space at the end
        '''
        self.assertTrue(Validator.contains_whitespace('there_is_a_space_at_the_end '))

    def test_contains_whitespace_space_in_the_middle(self):
        '''
        Tests the contains_whitespace method when there's a space in the middle
        '''
        self.assertTrue(Validator.contains_whitespace('there_is_a space_in_the_middle'))

    def test_contains_whitespace_only_a_space(self):
        '''
        Tests the contains_whitespace method when there's only whitespace
        '''
        self.assertTrue(Validator.contains_whitespace(' '))
    
    def test_contains_special_character_except_underscore_no_special_character(self):
        '''
        Tests the contains_special_character_except_underscore method when there is no special_character
        '''
        self.assertFalse(Validator.contains_special_character_except_underscore('no_special_character_in_string'))

    def test_contains_special_character_except_underscore_special_character_at_start(self):
        '''
        Tests the contains_special_character_except_underscore method when there's a special_character at the start
        '''
        self.assertTrue(Validator.contains_special_character_except_underscore('$there_was_a_special_character_over_there'))

    def test_contains_special_character_except_underscore_special_character_at_end(self):
        '''
        Tests the contains_special_character_except_underscore method when there's a special_character at the end
        '''
        self.assertTrue(Validator.contains_special_character_except_underscore('there_is_a_special_character_at_the_end*'))

    def test_contains_special_character_except_underscore_special_character_in_the_middle(self):
        '''
        Tests the contains_special_character_except_underscore method when there's a special_character in the middle
        '''
        self.assertTrue(Validator.contains_special_character_except_underscore('there_is_a&special_character_in_the_middle'))

    def test_contains_special_character_except_underscore_only_a_special_character(self):
        '''
        Tests the contains_special_character_except_underscore method when there's only special_character
        '''
        self.assertTrue(Validator.contains_special_character_except_underscore('#'))

    def test_contains_special_character_except_underscore_underscore(self):
        '''
        Tests the contains_special_character_except_underscore method when there's an underscore
        '''
        self.assertFalse(Validator.contains_special_character_except_underscore('there_are_underscores_everywhere'))        

    def test_starts_with_alphabet(self):
        '''
        Tests the starts_without_alphabet method there's an alphabet at the start
        '''
        self.assertFalse(Validator.starts_without_alphabet('starts_with_alphabet'))

    def test_starts_without_alphabet(self):
        '''
        Tests the starts_without_alphabet method there's no alphabet at the start
        '''
        self.assertTrue(Validator.starts_without_alphabet('1starts_without_alphabet'))

    def test_ends_with_alphabet(self):
        '''
        Tests the ends_without_alphabet_or_number method there's an alphabet at the end
        '''
        self.assertFalse(Validator.ends_without_alphabet_or_number('ends_with_alphabet'))

    def test_ends_with_number(self):
        '''
        Tests the ends_without_alphabet_or_number method there's a number at the end
        '''
        self.assertFalse(Validator.ends_without_alphabet_or_number('ends_with_number1'))
       
    def test_ends_without_alphabet_or_number(self):
        '''
        Tests the ends_without_alphabet_or_number method there's no alphabet or number at the end
        '''
        self.assertTrue(Validator.ends_without_alphabet_or_number('ends_with_special_character$'))
                         
    def test_contains_capital_letter_no_capital_letter(self):
        '''
        Tests the contains_capital_letter method when there is no capital_letter
        '''
        self.assertFalse(Validator.contains_capital_letter('no_capital_letter_in_string'))

    def test_contains_capital_letter_capital_letter_at_start(self):
        '''
        Tests the contains_capital_letter method when there's a capital_letter at the start
        '''
        self.assertTrue(Validator.contains_capital_letter('There_was_a_capital_letter_over_there'))

    def test_contains_capital_letter_capital_letter_at_end(self):
        '''
        Tests the contains_capital_letter method when there's a capital_letter at the end
        '''
        self.assertTrue(Validator.contains_capital_letter('there_is_a_capital_letter_at_the_enD'))

    def test_contains_capital_letter_capital_letter_in_the_middle(self):
        '''
        Tests the contains_capital_letter method when there's a capital_letter in the middle
        '''
        self.assertTrue(Validator.contains_capital_letter('there_is_a_Capital_letter_in_the_middle'))

    def test_contains_capital_letter_only_a_capital_letter(self):
        '''
        Tests the contains_capital_letter method when there's only capital_letter
        '''
        self.assertTrue(Validator.contains_capital_letter('A'))

    def test_is_integer_with_numeric_string(self):
        '''
        Tests the is_integer method with a numeric string
        '''
        self.assertTrue(Validator.is_integer('123'))

    def test_is_integer_with_non_numeric_string(self):
        '''
        Tests the is_integer method with a non-numeric string
        '''
        self.assertFalse(Validator.is_integer('f123'))

    def test_is_integer_with_float(self):
        '''
        Tests the is_integer method returns False when given a literal float
        '''
        self.assertFalse(Validator.is_integer(9.99))

class TestICMName(unittest.TestCase):
    '''
    Tests the ICMName class
    '''

    def test_is_project_name_valid_with_valid_name(self):
        '''
        Tests the is_project_name_valid method with a valid project name
        '''
        self.assertTrue(ICMName.is_project_name_valid('i14socnd'))

    def test_is_project_name_valid_name_contains_a_space(self):
        '''
        Tests the is_project_name_valid method with a name that contains a space
        '''
        self.assertFalse(ICMName.is_project_name_valid('i14soc nd'))

    def test_is_variant_name_valid_with_valid_name(self):
        '''
        Tests the is_variant_name_valid method with a valid variant name
        '''
        self.assertTrue(ICMName.is_variant_name_valid('ar_lib'))

    def test_is_variant_name_valid_name_contains_a_space(self):
        '''
        Tests the is_variant_name_valid method with a name that contains a space
        '''
        self.assertFalse(ICMName.is_variant_name_valid('ar lib'))

    def test_is_variant_name_valid_name_contains_a_special_character(self):
        '''
        Tests the is_variant_name_valid method with a name that contains a special character
        '''
        self.assertFalse(ICMName.is_variant_name_valid('ar.lib'))

    def test_is_variant_name_valid_name_starts_without_alphabet(self):
        '''
        Tests the is_variant_name_valid method with a name that starts without an alphabet
        '''
        self.assertFalse(ICMName.is_variant_name_valid('1ar_lib'))
        
    def test_is_variant_name_valid_name_ends_without_alphabet_or_number(self):
        '''
        Tests the is_variant_name_valid method with a name that ends without an alphabet or number
        '''
        self.assertFalse(ICMName.is_variant_name_valid('ar_lib_'))

    def test_is_libtype_name_valid_with_valid_name(self):
        '''
        Tests the is_libtype_name_valid method with a valid libtype name
        '''
        self.assertTrue(ICMName.is_libtype_name_valid('rtl'))

    def test_is_libtype_name_valid_name_contains_a_space(self):
        '''
        Tests the is_libtype_name_valid method with a name that contains a space
        '''
        self.assertFalse(ICMName.is_libtype_name_valid('r t l'))

    def test_is_library_name_valid_with_valid_name(self):
        '''
        Tests the is_library_name_valid method with a valid name
        '''
        self.assertTrue(ICMName.is_library_name_valid('dev'))

    def test_is_library_name_valid_name_contains_a_space(self):
        '''
        Tests the is_library_name_valid method with a name that contains a space
        '''
        self.assertFalse(ICMName.is_library_name_valid('d ev'))

    def test_is_config_name_valid_with_valid_name(self):
        '''
        Tests the is_config_name_valid method with a valid name
        '''
        self.assertTrue(ICMName.is_config_name_valid('REL1.0ND5revA--foo__15ww123a'))

    def test_is_config_name_valid_name_contains_a_space(self):
        '''
        Tests the is_config_name_valid method with a name that contains a space
        '''
        self.assertFalse(ICMName.is_config_name_valid('REL3.0ND5revA--Minichip 3.0__15ww145a'))

    def test_is_release_number_valid_with_a_valid_number(self):
        '''
        Tests the is_release_number_valid method with a valid release number
        '''
        self.assertTrue(ICMName.is_release_number_valid('123'))

    def test_is_release_number_valid_with_a_non_numeric_release(self):
        '''
        Tests the is_release_number_valid method with a non-numeric release number
        '''
        self.assertFalse(ICMName.is_release_number_valid('12a3'))

    def test_is_release_number_valid_with_an_invalid_number(self):
        '''
        Tests the is_release_number_valid method with an invalid number
        '''
        self.assertFalse(ICMName.is_release_number_valid('0'))

class TestAlteraName(unittest.TestCase):
    '''
    Tests the AlteraName class
    '''

    def test_is_label_valid_with_valid_label(self):
        '''
        Tests the is_label_valid method with a valid label
        '''
        self.assertTrue(AlteraName.is_label_valid('Minichip_3.0'))

    def test_is_label_valid_with_label_that_contains_whitespace(self):
        '''
        Tests the is_label_valid method with a label that contains whitespace
        '''
        self.assertFalse(AlteraName.is_label_valid('Minichip 3.0'))

    def test_is_label_valid_with_label_that_contains_special_characters(self):
        '''
        Tests the is_label_valid method with a label that contains special characters
        '''
        self.assertFalse(AlteraName.is_label_valid('This!Is@Not%Valid,:'))


if __name__ == '__main__':
    unittest.main()
