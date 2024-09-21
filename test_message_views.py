"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
import unittest
from unittest import TestCase
from models import db, connect_db, Message, User
from flask import session


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY
from flask import g

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# Don't have WTForms use CSRF at all, since it's a pain to test

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler-test"
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.other_user = User.signup(username="otheruser",
                                      email="otheruser@test.com",
                                      password="otheruser",
                                      image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        self.app_context.pop()

    def test_add_message_logged_in(self):
        """Can user add a message when logged-in?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello Warbler!"}, follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            # Check if message was created
            msg = Message.query.filter_by(text="Hello Warbler!").one()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.text, "Hello Warbler!")
            self.assertEqual(msg.user_id, self.testuser.id)


    def test_add_message_logged_out(self):
        """Can user add a message when logged-out?"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello Warbler!"}, follow_redirects=True)

            # Ensure user is redirected to the login page
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized.", resp.data)

            # Ensure no message was created
            msg_count = Message.query.count()
            self.assertEqual(msg_count, 0)


    def test_delete_message_as_user(self):
        """Test that user can successfully delete own message."""

        # Create a message by the test user or user1
        msg = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Delete the message
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Ensure the message was deleted
            deleted_msg = Message.query.get(msg.id)
            self.assertIsNone(deleted_msg)


    def test_delete_message_as_another_user(self):
        """Test that a different user cannot delete other user's message."""
        # Create a message by the test user
        msg = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            # Log in as a different user
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.other_user.id

            # Try to delete the message
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Ensure the message still exists in the database
            non_deleted_msg = Message.query.get(msg.id)
            self.assertIsNotNone(non_deleted_msg)

            # Check for flash message
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)




    def test_view_message(self):
        """Test viewing a single message."""
        # Create a message by the test user.
        msg = Message(text="viewable message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/messages/{msg.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"viewable message", resp.data)


if __name__ == '__main__':
    unittest.main()