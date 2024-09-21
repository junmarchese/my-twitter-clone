"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
import unittest
from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

class UserModelTestCase(unittest.TestCase):
    """Test views for messages."""

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

        # Initialize test users
        self.testuser1 = User.signup(
            username="testuser1",
            email="testuser1@test.com",
            password="testpassword1",
            image_url=None
        )
        self.testuser2 = User.signup(
            username="testuser2",
            email="testuser2@test.com",
            password="testpassword2",
            image_url=None
        )
        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""
            
        db.session.rollback()
        db.drop_all()
        self.app_context.pop()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_user_repr(self):
        """Does the repr method work as expected?"""
        self.assertEqual(repr(self.testuser1), f"<User #{self.testuser1.id}: {self.testuser1.username}, {self.testuser1.email}>")

    
    def test_user_is_following_another_user(self):
        """Does is_following successfully detect when user1 is following user2?"""
        self.testuser1.following.append(self.testuser2)
        db.session.commit()

        self.assertTrue(self.testuser1.is_following(self.testuser2))


    def test_user_is_not_following_another_user(self):
        """Does is_following successfully detect when user1 is not following user2?"""
        self.assertFalse(self.testuser1.is_following(self.testuser2))


    def test_user_is_followed_by_another_user(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        self.testuser2.following.append(self.testuser1)
        db.session.commit()

        self.assertTrue(self.testuser1.is_followed_by(self.testuser2))

    
    def test_user_is_not_followed_by_another_user(self):
        """Does is_followed_by successfully detect when user1 is not followed by user2?"""
        self.assertFalse(self.testuser1.is_followed_by(self.testuser2))

    
    def test_create_user(self):
        """Does User.create successfully create a new user given valid credentials?"""
        user = User.signup(username="newuser", email="newuser@test.com", password="password", image_url=None)
        db.session.commit()

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@test.com")


    def test_create_user_fail_validations(self):
        """Does User.create fail to create a new user if any of the validations(unique, non-nullable) fail?"""
        user = User.signup(username=self.testuser1.username, email="duplicate@test.com", password="password", image_url=None)

        with self.assertRaises(IntegrityError):
            db.session.commit()


    def test_user_authentication(self):
        """Does User.authenticate successfully return a user with valid credentials?"""
        user = User.authenticate(self.testuser1.username, "testpassword1")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, self.testuser1.username)


    def test_invalid_username_authenticate(self):
        """Does User.authenticate fail with invalid username?"""
        self.assertFalse(User.authenticate("badusername", "testpassword1"))


    def test_invalid_password_authenticate(self):
        """Does User.authenticate fail with invalid password?"""
        self.assertFalse(User.authenticate(self.testuser1.username, "badpassword"))
    

if __name__ == '__main__':
    unittest.main()

