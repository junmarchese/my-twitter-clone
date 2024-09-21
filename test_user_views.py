import os
import unittest
from flask import session
from models import db, connect_db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

class UserViewsTestCase(unittest.TestCase):
    """Test views for Users."""

    def setUp(self):
        """Set up the test environment before all tests."""
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler-test"
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
       
        """Create test client, add sample data."""
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
       
        db.session.rollback()
       
        db.create_all()
       
        self.testuser1 = User.signup(
            username="testuser1",
            email="test1@test.com",
            password="test1password",
            image_url=None
        )
        self.testuser2 = User.signup(
            username="testuser2",
            email="test2@test.com",
            password="test2password",
            image_url=None
        )
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        self.app_context.pop()

    def test_show_following(self):
        """Can a logged-in user see the following page?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.get(f"/users/{self.testuser1.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Following", str(resp.data))


    def test_show_following_logged_out(self):
        """Is a logged-out user prohibited from seeing the following page?"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser1.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_follow_another_user(self):
        """Can a logged-in user follow another user?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Check if testuser1 is now following testuser2 in the database
            user1 = User.query.get(self.testuser1.id)
            user2 = User.query.get(self.testuser2.id)

            # Check that testuser1 is following testuser2
            self.assertTrue(user1.is_following(user2))
            self.assertIn("Following", str(resp.data))


    def test_follow_another_user_logged_out(self):
        """Is a logged-out user not allowed to follow other users?"""
        with self.client as c:
            resp = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_add_message_logged_in_user(self):
        """Can a logged-in user add a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post("/messages/new", data={"text": "Hello Warbler!"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Check that the message was added to the database
            msg = Message.query.filter_by(text="Hello Warbler!").first()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.text, "Hello Warbler!")


    def test_add_message_logged_out_user(self):
        """Is a logged-out user not allowed to add a message?"""
        with self.client as c:
            resp = c.post(f"/messages/new", data={"text": "Hello Warbler!"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))





    

    