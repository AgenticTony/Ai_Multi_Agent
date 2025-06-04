from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class VapiMessage(BaseModel):
    """Base Vapi message model"""
    type: str
    content: Optional[str] = None
    transcript: Optional[str] = None
    functionCall: Optional[Dict[str, Any]] = None


class VapiCall(BaseModel):
    """Vapi call information"""
    id: str
    phoneNumber: Optional[str] = None
    status: Optional[str] = None
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None


class VapiWebhookRequest(BaseModel):
    """Incoming webhook request from Vapi"""
    message: VapiMessage
    call: VapiCall
    timestamp: Optional[datetime] = None


class VapiWebhookResponse(BaseModel):
    """Response to Vapi webhook"""
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class FunctionCallRequest(BaseModel):
    """Function call request model"""
    name: str
    parameters: Dict[str, Any]


class FunctionCallResponse(BaseModel):
    """Function call response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class AppointmentRequest(BaseModel):
    """Appointment booking request"""
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., regex=r'^\+?[\d\s\-\(\)]+$')
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM AM/PM format")
    service: Optional[str] = Field(default="consultation", max_length=100)


class LeadCaptureRequest(BaseModel):
    """Lead capture request"""
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., regex=r'^\+?[\d\s\-\(\)]+$')
    email: Optional[str] = Field(default=None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    interest: Optional[str] = Field(default=None, max_length=500)


class ConfirmationRequest(BaseModel):
    """Confirmation sending request"""
    phone: Optional[str] = Field(default=None, regex=r'^\+?[\d\s\-\(\)]+$')
    email: Optional[str] = Field(default=None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    message: str = Field(..., min_length=1, max_length=1000)


class TransferRequest(BaseModel):
    """Call transfer request"""
    reason: Optional[str] = Field(default="Customer request", max_length=200)
    department: Optional[str] = Field(default="general", max_length=50)


class ConversationMessage(BaseModel):
    """Individual conversation message"""
    role: str = Field(..., regex=r'^(user|assistant|system)$')
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Conversation history for a call"""
    call_id: str
    messages: List[ConversationMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
