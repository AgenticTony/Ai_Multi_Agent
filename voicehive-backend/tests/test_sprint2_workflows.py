"""
Sprint 2 Test Workflows - Test the 5 mock call flows
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import our tools and agent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools import crm, calendar, notify
from memory import mem0
from agent_roxy import RoxyAgent


class TestSprint2Workflows:
    """Test the 5 mock call workflows for Sprint 2"""
    
    def setup_method(self):
        """Setup for each test"""
        self.agent = RoxyAgent()
        
        # Clear any existing data
        crm.crm_tool.leads.clear()
        calendar.calendar_tool.appointments.clear()
        notify.notification_tool.notifications.clear()
        mem0.memory_system.fallback_memory.clear()
        mem0.memory_system.session_memories.clear()
    
    @pytest.mark.asyncio
    async def test_workflow_1_new_appointment_booking(self):
        """Test Workflow 1: New appointment booking"""
        print("\n=== Testing Workflow 1: New Appointment Booking ===")
        
        # Simulate incoming call data
        call_data = {
            "call": {
                "id": "call_001",
                "customer": {"number": "+1234567890"}
            },
            "message": {
                "content": "Hi, I'd like to book an appointment for next week"
            }
        }
        
        # Handle initial message
        response = await self.agent.handle_message(call_data)
        print(f"Agent Response: {response['message']}")
        
        # Simulate function call for booking
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "message": {
                "functionCall": {
                    "name": "book_appointment",
                    "parameters": {
                        "name": "John Smith",
                        "phone": "+1234567890",
                        "email": "john@example.com",
                        "date": tomorrow,
                        "time": "10:00 AM",
                        "service": "consultation"
                    }
                }
            }
        }
        
        booking_response = await self.agent.handle_function_call(booking_data)
        print(f"Booking Result: {booking_response}")
        
        # Verify appointment was created
        appointments = calendar.calendar_tool.appointments
        assert len(appointments) == 1
        
        # Verify lead was created
        leads = crm.crm_tool.leads
        assert len(leads) == 1
        
        # Verify notification was sent (simulated)
        notifications = notify.notification_tool.notifications
        assert len(notifications) >= 1
        
        # Verify memory was stored
        memories = mem0.memory_system.fallback_memory
        assert len(memories) >= 1
        
        print("✅ Workflow 1 completed successfully!")
        return {
            "workflow": "new_appointment_booking",
            "status": "success",
            "appointments_created": len(appointments),
            "leads_created": len(leads),
            "notifications_sent": len(notifications),
            "memories_stored": len(memories)
        }
    
    @pytest.mark.asyncio
    async def test_workflow_2_rescheduling(self):
        """Test Workflow 2: Rescheduling existing appointment"""
        print("\n=== Testing Workflow 2: Rescheduling ===")
        
        # First, create an existing appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        existing_booking = await calendar.book_appointment(
            "Jane Doe", "+1987654321", tomorrow, "2:00 PM", "consultation", "jane@example.com"
        )
        appointment_id = existing_booking["appointment_id"]
        
        # Simulate rescheduling call
        call_data = {
            "call": {
                "id": "call_002",
                "customer": {"number": "+1987654321"}
            },
            "message": {
                "content": "I need to reschedule my appointment"
            }
        }
        
        response = await self.agent.handle_message(call_data)
        print(f"Agent Response: {response['message']}")
        
        # Simulate function call for rescheduling
        new_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        reschedule_data = {
            "message": {
                "functionCall": {
                    "name": "reschedule_appointment",
                    "parameters": {
                        "appointment_id": appointment_id,
                        "new_date": new_date,
                        "new_time": "3:00 PM"
                    }
                }
            }
        }
        
        reschedule_response = await self.agent.handle_function_call(reschedule_data)
        print(f"Reschedule Result: {reschedule_response}")
        
        # Verify appointment was rescheduled
        appointment = calendar.get_appointment(appointment_id)
        assert appointment["success"]
        assert appointment["appointment"]["date"] == new_date
        assert appointment["appointment"]["time"] == "3:00 PM"
        
        print("✅ Workflow 2 completed successfully!")
        return {
            "workflow": "rescheduling",
            "status": "success",
            "appointment_rescheduled": True
        }
    
    @pytest.mark.asyncio
    async def test_workflow_3_cancellation(self):
        """Test Workflow 3: Appointment cancellation"""
        print("\n=== Testing Workflow 3: Cancellation ===")
        
        # First, create an existing appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        existing_booking = await calendar.book_appointment(
            "Bob Wilson", "+1555123456", tomorrow, "11:00 AM", "consultation", "bob@example.com"
        )
        appointment_id = existing_booking["appointment_id"]
        
        # Simulate cancellation call
        call_data = {
            "call": {
                "id": "call_003",
                "customer": {"number": "+1555123456"}
            },
            "message": {
                "content": "I need to cancel my appointment"
            }
        }
        
        response = await self.agent.handle_message(call_data)
        print(f"Agent Response: {response['message']}")
        
        # Simulate function call for cancellation
        cancel_data = {
            "message": {
                "functionCall": {
                    "name": "cancel_appointment",
                    "parameters": {
                        "appointment_id": appointment_id,
                        "reason": "Schedule conflict"
                    }
                }
            }
        }
        
        cancel_response = await self.agent.handle_function_call(cancel_data)
        print(f"Cancel Result: {cancel_response}")
        
        # Verify appointment was cancelled
        appointment = calendar.get_appointment(appointment_id)
        assert appointment["success"]
        assert appointment["appointment"]["status"] == "cancelled"
        
        print("✅ Workflow 3 completed successfully!")
        return {
            "workflow": "cancellation",
            "status": "success",
            "appointment_cancelled": True
        }
    
    @pytest.mark.asyncio
    async def test_workflow_4_objection_response(self):
        """Test Workflow 4: Handling objections"""
        print("\n=== Testing Workflow 4: Objection Response ===")
        
        # Simulate objection call
        call_data = {
            "call": {
                "id": "call_004",
                "customer": {"number": "+1444555666"}
            },
            "message": {
                "content": "Your service is too expensive, I can't afford it"
            }
        }
        
        response = await self.agent.handle_message(call_data)
        print(f"Agent Response: {response['message']}")
        
        # Follow up with more objections
        follow_up_data = {
            "call": {
                "id": "call_004",
                "customer": {"number": "+1444555666"}
            },
            "message": {
                "content": "I'm not sure if this is right for me"
            }
        }
        
        follow_up_response = await self.agent.handle_message(follow_up_data)
        print(f"Follow-up Response: {follow_up_response['message']}")
        
        # Eventually capture lead despite objections
        lead_data = {
            "message": {
                "functionCall": {
                    "name": "capture_lead",
                    "parameters": {
                        "name": "Sarah Johnson",
                        "phone": "+1444555666",
                        "email": "sarah@example.com",
                        "interest": "consultation",
                        "issue": "price concerns"
                    }
                }
            }
        }
        
        lead_response = await self.agent.handle_function_call(lead_data)
        print(f"Lead Capture Result: {lead_response}")
        
        # Verify lead was captured with objection notes
        leads = crm.crm_tool.leads
        assert len(leads) >= 1
        
        # Find the lead and check for notes
        lead_found = False
        for lead in leads.values():
            if lead.phone == "+1444555666":
                lead_found = True
                assert "price concerns" in lead.issue
                break
        
        assert lead_found
        
        print("✅ Workflow 4 completed successfully!")
        return {
            "workflow": "objection_response",
            "status": "success",
            "objections_handled": True,
            "lead_captured": True
        }
    
    @pytest.mark.asyncio
    async def test_workflow_5_faq_fallback(self):
        """Test Workflow 5: FAQ and fallback to human"""
        print("\n=== Testing Workflow 5: FAQ Fallback ===")
        
        # Simulate FAQ question
        call_data = {
            "call": {
                "id": "call_005",
                "customer": {"number": "+1777888999"}
            },
            "message": {
                "content": "What are your business hours?"
            }
        }
        
        response = await self.agent.handle_message(call_data)
        print(f"Agent Response: {response['message']}")
        
        # Simulate complex question requiring human transfer
        complex_question_data = {
            "call": {
                "id": "call_005",
                "customer": {"number": "+1777888999"}
            },
            "message": {
                "content": "I have a very specific technical question about your proprietary algorithm implementation"
            }
        }
        
        complex_response = await self.agent.handle_message(complex_question_data)
        print(f"Complex Question Response: {complex_response['message']}")
        
        # Simulate transfer to human
        transfer_data = {
            "message": {
                "functionCall": {
                    "name": "transfer_call",
                    "parameters": {
                        "reason": "Complex technical question",
                        "department": "technical_support"
                    }
                }
            }
        }
        
        transfer_response = await self.agent.handle_function_call(transfer_data)
        print(f"Transfer Result: {transfer_response}")
        
        # Verify transfer was initiated
        assert transfer_response["result"]["success"]
        assert "transfer" in transfer_response["result"]["message"].lower()
        
        print("✅ Workflow 5 completed successfully!")
        return {
            "workflow": "faq_fallback",
            "status": "success",
            "faq_handled": True,
            "transfer_initiated": True
        }
    
    @pytest.mark.asyncio
    async def test_all_workflows_integration(self):
        """Run all workflows and verify data storage/retrieval"""
        print("\n=== Running All Workflows Integration Test ===")
        
        results = []
        
        # Run all workflows
        results.append(await self.test_workflow_1_new_appointment_booking())
        results.append(await self.test_workflow_2_rescheduling())
        results.append(await self.test_workflow_3_cancellation())
        results.append(await self.test_workflow_4_objection_response())
        results.append(await self.test_workflow_5_faq_fallback())
        
        # Verify overall data integrity
        print("\n=== Final Data Verification ===")
        
        # Check CRM stats
        crm_stats = crm.get_crm_stats()
        print(f"CRM Stats: {crm_stats}")
        
        # Check memory system
        total_memories = len(mem0.memory_system.fallback_memory)
        print(f"Total Memories Stored: {total_memories}")
        
        # Check notifications
        total_notifications = len(notify.notification_tool.notifications)
        print(f"Total Notifications Sent: {total_notifications}")
        
        # Verify data is retrievable from Mem0
        if total_memories > 0:
            # Test memory search
            search_result = mem0.search_memories("appointment", limit=5)
            print(f"Memory Search Results: {search_result['count'] if search_result['success'] else 0} found")
        
        print("\n✅ All workflows completed successfully!")
        
        return {
            "integration_test": "success",
            "workflows_completed": len(results),
            "total_leads": crm_stats["total_leads"] if crm_stats["success"] else 0,
            "total_memories": total_memories,
            "total_notifications": total_notifications,
            "results": results
        }


if __name__ == "__main__":
    """Run the tests directly"""
    import asyncio
    
    async def run_tests():
        test_instance = TestSprint2Workflows()
        
        print("🚀 Starting Sprint 2 Workflow Tests...")
        
        try:
            # Run integration test (which runs all workflows)
            final_result = await test_instance.test_all_workflows_integration()
            
            print("\n" + "="*50)
            print("📊 FINAL TEST RESULTS")
            print("="*50)
            print(json.dumps(final_result, indent=2))
            print("\n🎉 All Sprint 2 workflows tested successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Run the tests
    asyncio.run(run_tests())
