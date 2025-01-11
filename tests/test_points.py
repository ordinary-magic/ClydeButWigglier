import unittest
from unittest.mock import patch, MagicMock
from lib.Responses import points
from helpers import get_mock_discord_message, get_response
from datetime import datetime, timedelta

class TestPoints(unittest.TestCase):
    to = points.Points()

    POINTS = [(1,300),(2, 1.11111),(3,-2)]

    # Test !points
    @patch('lib.Responses.points.ServerDatabase.get_points', return_value=POINTS)
    @patch('lib.Responses.points.ServerDatabase.get_value', return_value='Dollars')
    def test_points(self, mock_name, mock_points):
        request = get_mock_discord_message(guildid=69)
        
        with patch('lib.Responses.points.get_username_from_id', return_value='name'):
            actual, context = get_response(self.to, "", request)

        expected = 'The Current Scores Are:' +\
            '\n1. 300 Dollars - name' +\
            '\n2. 1.111 Dollars - name' +\
            '\n3. -2 Dollars - name'
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_points.assert_called_once()
        mock_name.assert_called_once_with(0, 'point_name', 'static_vars')

    # Test !points with no points
    @patch('lib.Responses.points.ServerDatabase.get_points', return_value=[])
    def test_points_no_values(self, mock):
        request = get_mock_discord_message(guildid=69)
        
        with patch('lib.Responses.points.get_username_from_id', return_value='name'):
            actual, context = get_response(self.to, "", request)

        expected = "Nobody has any points yet :("
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock.assert_called_once()

    # Test user not appointed error message
    @patch('lib.Responses.points.Points.is_appointed', return_value=False)
    def test_is_appointed_response(self, mock):
        request = get_mock_discord_message(guildid=69, author_id=420)
        
        with patch('lib.Responses.points.get_username_from_id', return_value='name'):
            actual, context = get_response(self.to, "add 300", request)

        expected = "Sorry, you don't have clearance for that. :spy:"
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock.assert_called_once_with(420, 69, True)

    # Test is_appointed with no appointee
    @patch('lib.Responses.points.Points.is_deputized', return_value=False)
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=None)
    def test_is_appointed_no_appointee(self, mock_db, mock_deputy):        
        self.assertTrue(self.to.is_appointed(420, 69, True))
        mock_db.assert_called_once_with(points.POINT_APPOINTEE, 'point_role')
        mock_deputy.assert_not_called()
        
    # Test is_appointed with different appointee
    @patch('lib.Responses.points.Points.is_deputized', return_value=False)
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=300)
    def test_is_appointed_different_appointee(self, mock_db, mock_deputy):        
        self.assertFalse(self.to.is_appointed(420, 69, True))
        mock_db.assert_called_once_with(points.POINT_APPOINTEE, 'point_role')
        mock_deputy.assert_called_once_with(420, 69)
        
    # Test is_appointed when it is the correct user
    @patch('lib.Responses.points.Points.is_deputized', return_value=False)
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=420)
    def test_is_appointed_is_appointee(self, mock_db, mock_deputy):        
        self.assertTrue(self.to.is_appointed(420, 69, True))
        mock_db.assert_called_once_with(points.POINT_APPOINTEE, 'point_role')
        mock_deputy.assert_not_called()
                
    # Test is_appointed with a deputy authorization
    @patch('lib.Responses.points.Points.is_deputized', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=300)
    def test_is_appointed_is_deputy_and_allowed(self, mock_db, mock_deputy):        
        self.assertTrue(self.to.is_appointed(420, 69, True))
        mock_db.assert_called_once_with(points.POINT_APPOINTEE, 'point_role')
        mock_deputy.assert_called_once_with(420, 69)
                        
    # Test is_appointed without a deputy authorization
    @patch('lib.Responses.points.Points.is_deputized', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=300)
    def test_is_appointed_is_deputy_and_disallowed(self, mock_db, mock_deputy):        
        self.assertFalse(self.to.is_appointed(420, 69, False))
        mock_db.assert_called_once_with(points.POINT_APPOINTEE, 'point_role')
        mock_deputy.assert_not_called() 
        
    # Test is_deputized with a valid deputy
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=420)
    def test_is_deputized_valid(self, mock_db):
        self.to.deputy_timeout = datetime.now() + timedelta(minutes=1)        
        self.assertTrue(self.to.is_deputized(420, 69))
        mock_db.assert_called_once_with(points.DEPUTY_POINT_APOINTEE, 'point_role')
        
    # Test is_deputized when time has run out
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=420)
    def test_is_deputized_after_timeout(self, mock_db):
        self.to.deputy_timeout = datetime.min 
        self.assertFalse(self.to.is_deputized(420, 69))
        mock_db.assert_not_called()

    # Test is_deputized with the wrong deputy
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=330)
    def test_is_deputized_wrong_user(self, mock_db):
        self.to.deputy_timeout = datetime.now() + timedelta(minutes=1)     
        self.assertFalse(self.to.is_deputized(420, 69))
        mock_db.assert_called_once_with(points.DEPUTY_POINT_APOINTEE, 'point_role')

    # Test !points reset   
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.initialize_column')
    @patch('lib.Responses.points.ServerDatabase.get_value', return_value='Dollars')
    def test_points_reset(self, mock_name, mock_db, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420)
        
        actual, context = get_response(self.to, "reset", request)

        expected = "Everyone's hard-earned Dollars have been reset! :disguised_face:"
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_db.assert_called_once_with('points', 0)
        mock_name.assert_called_once_with(0, 'point_name', 'static_vars')
        mock_appointed.assert_called_once_with(420, 69, False)

        
    # Test no mentions
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_points_no_mentions(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420)
        
        actual, context = get_response(self.to, "add 5", request)

        expected = "Woah friendo, seems like you typoed something. Check \"!help points\" and try again. :sweat:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, True)

                
    # Test improper command formatting   
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_points_improper_formatting(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[11,22])
        
        actual, context = get_response(self.to, "add", request)

        expected = "Woah friendo, seems like you typoed something. Check \"!help points\" and try again. :sweat:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, True)

    # Test !points appoint yourself   
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_points_appoint_yourself(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[420])
        
        actual, context = get_response(self.to, "appoint moolah", request)

        expected = "You can't Point-Appoint yourself! Thats Illegal!"
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, False)

    # Test !points appoint   
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.initialize_column')
    @patch('lib.Responses.points.ServerDatabase.set_value')
    def test_points_appoint(self, mock_set, mock_initialize, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "appoint moolah", request)

        expected = ":tada: Let it be known that from this day forth, <@100> shall be ruler and Chief Point-Apointee of \"moolah\"! :tada:"
    
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, False)
        mock_initialize.assert_called_once_with('point_role', '')
        mock_set.assert_any_call(100, 'point_role', points.POINT_APPOINTEE)
        mock_set.assert_any_call(0, 'point_name', 'moolah', 'static_vars')
        
    # Test invalid number for add or deputize   
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_points_invalid_number(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "add bob", request)

        expected = "Sorry, but \"bob\" isnt a valid floating point number. :nerd:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, True)
   
    # Test !points add X
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.add_to_value')
    def test_points_add(self, mock_add, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "add -5.13", request)

        self.assertEqual(actual, None)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, True)
        mock_add.assert_called_once_with(100, 'points', -5.13)
           
    # Test !points add X @user
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.add_to_value')
    def test_points_add_with_text_user(self, mock_add, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "add 5.13 <@100>", request)

        self.assertEqual(actual, None)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, True)
        mock_add.assert_called_once_with(100, 'points', 5.13)
        
    # Test !points deputize X
    @patch('lib.Responses.points.Points.name', return_value='moolah')
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.set_value')
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=330)
    def test_points_deputize(self, mock_get, mock_set, mock_appointed, _):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "deputize 3", request)

        expected = "<@100> has been appointed loyal Deputy-Point-Apointee of moolah! (for the next 3.0 minutes anyway) :cowboy:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        self.assertAlmostEqual(self.to.deputy_timeout, datetime.now() + timedelta(minutes=3), delta=timedelta(seconds=1))

        mock_appointed.assert_called_once_with(420, 69, False)
        mock_get.assert_called_once_with(points.DEPUTY_POINT_APOINTEE, 'point_role')
        mock_set.assert_any_call(330, 'point_role', '')
        mock_set.assert_any_call(100, 'point_role', points.DEPUTY_POINT_APOINTEE)
           
    # Test !points deputize X @user
    @patch('lib.Responses.points.Points.name', return_value='moolah')
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    @patch('lib.Responses.points.ServerDatabase.set_value')
    @patch('lib.Responses.points.ServerDatabase.get_special_user', return_value=330)
    def test_points_deputize_user(self, mock_get, mock_set, mock_appointed, _):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[100])
        
        actual, context = get_response(self.to, "deputize 3.5 <@100>", request)

        expected = "<@100> has been appointed loyal Deputy-Point-Apointee of moolah! (for the next 3.5 minutes anyway) :cowboy:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        self.assertAlmostEqual(self.to.deputy_timeout, datetime.now() + timedelta(minutes=3.5), delta=timedelta(seconds=1))

        mock_appointed.assert_called_once_with(420, 69, False)
        mock_get.assert_called_once_with(points.DEPUTY_POINT_APOINTEE, 'point_role')
        mock_set.assert_any_call(330, 'point_role', '')
        mock_set.assert_any_call(100, 'point_role', points.DEPUTY_POINT_APOINTEE)

    # Test !points deputize X on yourself
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_points_deputize_yourself(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[420])
        
        actual, context = get_response(self.to, "deputize 3", request)

        expected = "You can't nominate yourself Point-Appointee and Deputy Point-Appointee! Thats Illegal!"
            
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, False)

    # !points with a bad command flag
    @patch('lib.Responses.points.Points.is_appointed', return_value=True)
    def test_bad_command(self, mock_appointed):
        request = get_mock_discord_message(guildid=69, author_id=420, mentions=[420])
        
        actual, context = get_response(self.to, "give me points", request)

        expected = "Woah friendo, seems like you typoed something. Check \"!help points\" and try again. :pensive:"

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)
        mock_appointed.assert_called_once_with(420, 69, False)