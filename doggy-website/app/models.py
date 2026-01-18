from app import db
from datetime import datetime, timedelta

class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    media = db.relationship('Media', backref='entry', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='entry_tags', backref='entries', lazy=True)

    def __repr__(self):
        return f'<DiaryEntry {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_name': self.location_name,
            'media': [m.to_dict() for m in self.media],
            'tags': [t.name for t in self.tags]
        }


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
    file_path = db.Column(db.String(500), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('diary_entry.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'media_type': self.media_type,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


# Association table for many-to-many relationship
entry_tags = db.Table('entry_tags',
    db.Column('entry_id', db.Integer, db.ForeignKey('diary_entry.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


# ============================================
# TRAINING RESOURCE MODELS
# ============================================

# Association table for TrainingResource <-> ResourceCategory (many-to-many)
resource_categories = db.Table('resource_categories',
    db.Column('resource_id', db.Integer, db.ForeignKey('training_resource.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('resource_category.id'), primary_key=True)
)

# Association table for TrainingResource <-> ResourceTag (many-to-many)
resource_tags = db.Table('resource_tags',
    db.Column('resource_id', db.Integer, db.ForeignKey('training_resource.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('resource_tag.id'), primary_key=True)
)

# Association table for WeeklyActivity <-> TrainingResource (many-to-many)
activity_resources = db.Table('activity_resources',
    db.Column('activity_id', db.Integer, db.ForeignKey('weekly_activity.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('training_resource.id'), primary_key=True)
)


class ResourceCategory(db.Model):
    """Categories for organizing training resources (e.g., 'Obedience', 'Agility', 'Health')"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#8B4513')  # Hex color for UI display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ResourceCategory {self.name}>'


class ResourceTag(db.Model):
    """Tags for fine-grained organization of training resources"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<ResourceTag {self.name}>'


class TrainingResource(db.Model):
    """Files stored in the training repository"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # File information
    filename = db.Column(db.String(300), nullable=False)  # Stored filename (timestamped)
    original_filename = db.Column(db.String(300), nullable=False)  # Original name for display
    file_path = db.Column(db.String(500), nullable=False)  # Relative path: 'uploads/training/...'
    file_type = db.Column(db.String(50), nullable=False)  # Category: 'document', 'video', 'image', etc.
    file_extension = db.Column(db.String(20), nullable=False)  # e.g., 'pdf', 'mp4', 'docx'
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    categories = db.relationship('ResourceCategory', secondary='resource_categories',
                                  backref=db.backref('resources', lazy='dynamic'), lazy=True)
    tags = db.relationship('ResourceTag', secondary='resource_tags',
                           backref=db.backref('resources', lazy='dynamic'), lazy=True)

    def __repr__(self):
        return f'<TrainingResource {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'categories': [c.name for c in self.categories],
            'tags': [t.name for t in self.tags],
            'created_at': self.created_at.isoformat()
        }

    @property
    def file_size_formatted(self):
        """Return human-readable file size"""
        if not self.file_size:
            return 'Unknown'
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def icon_class(self):
        """Return Bootstrap icon class based on file type"""
        icons = {
            'document': 'bi-file-earmark-text',
            'video': 'bi-file-earmark-play',
            'image': 'bi-file-earmark-image',
            'spreadsheet': 'bi-file-earmark-spreadsheet',
            'presentation': 'bi-file-earmark-slides',
            'other': 'bi-file-earmark'
        }
        return icons.get(self.file_type, 'bi-file-earmark')


# ============================================
# TRAINING PROGRAM MODELS
# ============================================

class TrainingProgram(db.Model):
    """A training program with weekly template activities"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Duration settings
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # NULL = ongoing program
    is_ongoing = db.Column(db.Boolean, default=False)

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    weekly_activities = db.relationship('WeeklyActivity', backref='program',
                                         lazy=True, cascade='all, delete-orphan',
                                         order_by='WeeklyActivity.day_of_week, WeeklyActivity.time')

    def __repr__(self):
        return f'<TrainingProgram {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_ongoing': self.is_ongoing,
            'is_active': self.is_active,
            'weekly_activities': [a.to_dict() for a in self.weekly_activities],
            'created_at': self.created_at.isoformat()
        }

    @property
    def duration_weeks(self):
        """Calculate duration in weeks, or None if ongoing"""
        if self.is_ongoing or not self.end_date:
            return None
        delta = self.end_date - self.start_date
        return delta.days // 7

    @property
    def status_label(self):
        """Return human-readable status"""
        from datetime import date
        today = date.today()
        if not self.is_active:
            return 'Inactive'
        if today < self.start_date:
            return 'Scheduled'
        if self.is_ongoing or (self.end_date and today <= self.end_date):
            return 'Active'
        return 'Completed'

    def get_activities_for_day(self, day_of_week):
        """Get all activities for a specific day (0=Monday, 6=Sunday)"""
        return [a for a in self.weekly_activities if a.day_of_week == day_of_week]


class WeeklyActivity(db.Model):
    """A template activity that repeats each week on a specific day"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Schedule
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    time = db.Column(db.Time, nullable=True)  # Optional specific time
    duration_minutes = db.Column(db.Integer, nullable=True)  # Optional duration

    # Foreign key to program
    program_id = db.Column(db.Integer, db.ForeignKey('training_program.id'), nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships - resources referenced by this activity
    resources = db.relationship('TrainingResource', secondary='activity_resources',
                                 backref=db.backref('activities', lazy='dynamic'), lazy=True)

    # Class-level constant for day names
    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __repr__(self):
        return f'<WeeklyActivity {self.name} on {self.day_name}>'

    @property
    def day_name(self):
        """Return the name of the day"""
        return self.DAY_NAMES[self.day_of_week]

    @property
    def time_formatted(self):
        """Return formatted time string"""
        if self.time:
            return self.time.strftime('%I:%M %p')
        return None

    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        if not self.duration_minutes:
            return None
        hours, mins = divmod(self.duration_minutes, 60)
        if hours and mins:
            return f"{hours}h {mins}m"
        elif hours:
            return f"{hours}h"
        return f"{mins}m"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'day_of_week': self.day_of_week,
            'day_name': self.day_name,
            'time': self.time.isoformat() if self.time else None,
            'time_formatted': self.time_formatted,
            'duration_minutes': self.duration_minutes,
            'duration_formatted': self.duration_formatted,
            'program_id': self.program_id,
            'resources': [r.to_dict() for r in self.resources]
        }


# ============================================
# APPOINTMENT MODELS
# ============================================

class AppointmentType:
    """Predefined appointment types with display info"""
    VET = 'vet'
    GROOMING = 'grooming'
    TRAINING_CLASS = 'training_class'
    VACCINATION = 'vaccination'
    CHECKUP = 'checkup'
    OTHER = 'other'

    CHOICES = [
        (VET, 'Vet Visit', '#28a745'),           # Green
        (GROOMING, 'Grooming', '#17a2b8'),        # Cyan
        (TRAINING_CLASS, 'Training Class', '#007bff'),  # Blue
        (VACCINATION, 'Vaccination', '#dc3545'),  # Red
        (CHECKUP, 'Checkup', '#fd7e14'),         # Orange
        (OTHER, 'Other', '#6c757d'),             # Gray
    ]

    @classmethod
    def get_color(cls, type_key):
        for key, label, color in cls.CHOICES:
            if key == type_key:
                return color
        return '#6c757d'

    @classmethod
    def get_label(cls, type_key):
        for key, label, color in cls.CHOICES:
            if key == type_key:
                return label
        return 'Other'


class RecurrenceFrequency:
    """Recurrence frequency options"""
    NONE = 'none'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    EVERY_2_MONTHS = 'every_2_months'
    EVERY_3_MONTHS = 'every_3_months'
    EVERY_6_MONTHS = 'every_6_months'
    YEARLY = 'yearly'

    CHOICES = [
        (NONE, 'Does not repeat'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (EVERY_2_MONTHS, 'Every 2 months'),
        (EVERY_3_MONTHS, 'Every 3 months'),
        (EVERY_6_MONTHS, 'Every 6 months'),
        (YEARLY, 'Yearly'),
    ]


class Appointment(db.Model):
    """Individual appointment record"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False, default='other')

    # Date/Time
    date_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True, default=60)

    # Location
    location = db.Column(db.String(300), nullable=True)

    # Details
    notes = db.Column(db.Text, nullable=True)

    # Reminder (minutes before)
    reminder_minutes = db.Column(db.Integer, nullable=True)

    # Recurrence tracking
    parent_appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    recurrence_frequency = db.Column(db.String(20), nullable=True)
    recurrence_end_date = db.Column(db.Date, nullable=True)

    # Status
    is_completed = db.Column(db.Boolean, default=False)
    is_cancelled = db.Column(db.Boolean, default=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential relationship for recurring appointments
    child_appointments = db.relationship(
        'Appointment',
        backref=db.backref('parent_appointment', remote_side=[id]),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Appointment {self.title} on {self.date_time}>'

    @property
    def type_label(self):
        return AppointmentType.get_label(self.appointment_type)

    @property
    def type_color(self):
        return AppointmentType.get_color(self.appointment_type)

    @property
    def end_time(self):
        """Calculate end time based on duration"""
        if self.duration_minutes:
            return self.date_time + timedelta(minutes=self.duration_minutes)
        return self.date_time

    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        if not self.duration_minutes:
            return None
        hours, mins = divmod(self.duration_minutes, 60)
        if hours and mins:
            return f"{hours}h {mins}m"
        elif hours:
            return f"{hours}h"
        return f"{mins}m"

    @property
    def is_recurring(self):
        return self.recurrence_frequency and self.recurrence_frequency != 'none'

    @property
    def is_part_of_series(self):
        return self.parent_appointment_id is not None

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'appointment_type': self.appointment_type,
            'type_label': self.type_label,
            'type_color': self.type_color,
            'date_time': self.date_time.isoformat(),
            'duration_minutes': self.duration_minutes,
            'duration_formatted': self.duration_formatted,
            'location': self.location,
            'notes': self.notes,
            'reminder_minutes': self.reminder_minutes,
            'is_completed': self.is_completed,
            'is_cancelled': self.is_cancelled,
            'is_recurring': self.is_recurring,
            'is_part_of_series': self.is_part_of_series,
        }

    def to_calendar_event(self):
        """Convert to FullCalendar event format"""
        return {
            'id': f'appointment-{self.id}',
            'title': self.title,
            'start': self.date_time.isoformat(),
            'end': self.end_time.isoformat() if self.duration_minutes else None,
            'color': self.type_color,
            'extendedProps': {
                'type': 'appointment',
                'appointmentType': self.appointment_type,
                'typeLabel': self.type_label,
                'location': self.location,
                'url': f'/appointments/{self.id}'
            }
        }
