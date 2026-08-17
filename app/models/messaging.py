from datetime import datetime
from app.models import db

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    conversation_type = db.Column(db.String(30), default='Direct', nullable=False) # Direct, Group, Announcement
    title = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    school = db.relationship('School', lazy=True)
    participants = db.relationship('ConversationParticipant', backref='conversation', cascade='all, delete-orphan', lazy=True)
    messages = db.relationship('Message', backref='conversation', cascade='all, delete-orphan', lazy=True, order_by='Message.created_at.asc()')

    def __repr__(self):
        return f'<Conversation #{self.id} Type={self.conversation_type} School={self.school_id}>'


class ConversationParticipant(db.Model):
    __tablename__ = 'conversation_participants'
    __table_args__ = (
        db.UniqueConstraint('conversation_id', 'user_id', name='uq_conversation_participant'),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<ConversationParticipant Conv #{self.conversation_id} User #{self.user_id}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sender = db.relationship('User', lazy=True)
    read_states = db.relationship('MessageReadState', backref='message', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Message #{self.id} Conv #{self.conversation_id} Sender #{self.sender_id}>'


class MessageReadState(db.Model):
    __tablename__ = 'message_read_states'
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='uq_message_user_read'),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<MessageReadState Msg #{self.message_id} User #{self.user_id}>'
