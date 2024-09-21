import os
import unittest
from models import db, User, Message
from sqlalchemy.exc import IntegrityError


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app


class MessageModelTestCase(unittest.TestCase):
    """Test the Message model."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment before all tests."""
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler-test"
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    def setUp(self):
        """Create test client, add sample data."""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        self.testuser = User.signup(
                username="testuser",
                email="test@test.com",
                password="testpassword",
                image_url=None
        )
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
       
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_message_model(self):
        """Does the model work?"""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Test message",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        # User should have one message and that message text matches. 
        self.assertEqual(len(user.messages), 1)
        self.assertEqual(user.messages[0].text, "Test message")


    def test_message_user_id(self):
        """Is the user_id associated with the message correct?"""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Test message",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(msg.user_id, user.id)

    
    def test_message_repr(self):
        """Does the __repr__ method work as expected?"""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Test message",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(
            repr(msg),
            f"<Message #{msg.id}: {msg.text}, User #{msg.user_id}>"
        )

    
    def test_message_no_text(self):
        """Does creating a message without text fail?"""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text=None,
            user_id=user.id
        )

        db.session.add(msg)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    
    def test_message_association_with_user(self):
        """Test if the message is associated with the correct user."""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Another message",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        self.assertIn(msg, user.messages)


    def test_message_deletion(self):
        """Test if a message can be deleted."""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Message to be deleted",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        db.session.delete(msg)
        db.session.commit()

        self.assertEqual(Message.query.count(), 0)


    def test_message_timestamp(self):
        """Test if the message has a timestamp."""
        user = db.session.get(User, self.testuser.id)
        msg = Message(
            text="Message with timestamp",
            user_id=user.id
        )

        db.session.add(msg)
        db.session.commit()

        self.assertIsNotNone(msg.timestamp)

if __name__ == '__main__':
    unittest.main()






