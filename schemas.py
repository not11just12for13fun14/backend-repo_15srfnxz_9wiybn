"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# BrainDash Schemas

EnergyLevel = Literal["low", "medium", "high"]

class Task(BaseModel):
    """
    Tasks collection schema
    Collection name: "task"
    """
    text: str = Field(..., description="Raw task input from user")
    category: Optional[str] = Field(None, description="AI-detected category: admin, deep, creative, social, other")
    energy: Optional[EnergyLevel] = Field(None, description="Estimated energy required")
    urgency: Optional[int] = Field(None, ge=0, le=3, description="Urgency level 0=none,1=low,2=med,3=high")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Composite priority score 0-100")
    due: Optional[str] = Field(None, description="Parsed due descriptor, e.g., today, tomorrow, date string")
    tips: Optional[List[str]] = Field(default_factory=list, description="Helpful nudges or tips")
    mood: Optional[str] = Field(None, description="User mood if provided at creation time")
    user_energy: Optional[EnergyLevel] = Field(None, description="User self-reported energy at creation time")
    completed: bool = Field(False, description="Task completion state")

class MoodLog(BaseModel):
    """
    Mood logs collection schema
    Collection name: "moodlog"
    """
    mood: str = Field(..., description="User mood description or tag")
    energy: EnergyLevel = Field(..., description="User energy level")
    notes: Optional[str] = Field(None, description="Optional context notes")
    recorded_at: Optional[datetime] = Field(default=None, description="Timestamp auto-set on insert")

# Example schemas retained for reference (not used by BrainDash directly):
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
