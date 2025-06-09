"""
Prompt Management Service - Handles versioned prompts and updates
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Prompt version data structure"""
    version: str
    timestamp: str
    rationale: str
    status: str
    prompt: Dict[str, str]
    performance_metrics: Dict[str, float]
    feedback_data: Dict[str, Any]


class PromptManager:
    """Manages versioned prompts and updates"""
    
    def __init__(self, base_path: str = None):
        # Use a data directory for prompt storage
        if base_path is None:
            # Default to a data directory in the project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            base_path = os.path.join(project_root, "data", "prompts")
        
        self.base_path = base_path
        self.updates_file = os.path.join(self.base_path, "prompt_updates.json")
        self.prompts_dir = os.path.join(self.base_path, "versions")
        
        # Ensure directories exist
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # Load current state
        self._load_current_state()
    
    def _load_current_state(self):
        """Load current prompt management state"""
        try:
            if os.path.exists(self.updates_file):
                with open(self.updates_file, 'r') as f:
                    self.state = json.load(f)
            else:
                self.state = self._create_initial_state()
                self._save_state()
                
        except Exception as e:
            logger.error(f"Error loading prompt manager state: {str(e)}")
            self.state = self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial state structure"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "current_prompt_version": "v1.0",
            "prompt_history": [],
            "pending_improvements": [],
            "feedback_analysis": {
                "common_issues": [],
                "improvement_suggestions": [],
                "last_analysis_date": None
            }
        }
    
    def _save_state(self):
        """Save current state to file"""
        try:
            self.state["last_updated"] = datetime.now().isoformat()
            with open(self.updates_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving prompt manager state: {str(e)}")
    
    def get_current_prompt(self) -> Optional[PromptVersion]:
        """Get the current active prompt version"""
        try:
            current_version = self.state.get("current_prompt_version", "v1.0")
            return self.get_prompt_version(current_version)
        except Exception as e:
            logger.error(f"Error getting current prompt: {str(e)}")
            return None
    
    def get_prompt_version(self, version: str) -> Optional[PromptVersion]:
        """Get a specific prompt version"""
        try:
            prompt_file = os.path.join(self.prompts_dir, f"{version}.json")
            
            if not os.path.exists(prompt_file):
                logger.warning(f"Prompt version file not found: {prompt_file}")
                return None
            
            with open(prompt_file, 'r') as f:
                prompt_data = json.load(f)
            
            return PromptVersion(
                version=prompt_data.get("version", version),
                timestamp=prompt_data.get("timestamp", ""),
                rationale=prompt_data.get("rationale", ""),
                status=prompt_data.get("status", "unknown"),
                prompt=prompt_data.get("prompt", {}),
                performance_metrics=prompt_data.get("performance_metrics", {}),
                feedback_data=prompt_data.get("feedback_data", {})
            )
            
        except Exception as e:
            logger.error(f"Error loading prompt version {version}: {str(e)}")
            return None
    
    def create_new_version(self, base_version: str, changes: Dict[str, Any], 
                          rationale: str) -> Optional[str]:
        """Create a new prompt version based on an existing version"""
        try:
            # Load base version
            base_prompt = self.get_prompt_version(base_version)
            if not base_prompt:
                logger.error(f"Base version {base_version} not found")
                return None
            
            # Generate new version number
            new_version = self._generate_version_number()
            
            # Create new prompt data
            new_prompt_data = {
                "version": new_version,
                "timestamp": datetime.now().isoformat(),
                "rationale": rationale,
                "status": "pending",
                "prompt": {**base_prompt.prompt, **changes.get("prompt", {})},
                "performance_metrics": {
                    "booking_success_rate": 0.0,
                    "customer_satisfaction": 0.0,
                    "call_resolution_rate": 0.0,
                    "average_call_duration": 0.0,
                    "transfer_rate": 0.0
                },
                "feedback_data": {
                    "total_calls_analyzed": 0,
                    "common_issues": [],
                    "improvement_areas": [],
                    "positive_patterns": []
                },
                "base_version": base_version,
                "changes_applied": changes
            }
            
            # Save new version file
            prompt_file = os.path.join(self.prompts_dir, f"{new_version}.json")
            with open(prompt_file, 'w') as f:
                json.dump(new_prompt_data, f, indent=2)
            
            # Update history
            self.state["prompt_history"].append({
                "version": new_version,
                "timestamp": new_prompt_data["timestamp"],
                "rationale": rationale,
                "status": "pending",
                "base_version": base_version
            })
            
            self._save_state()
            
            logger.info(f"Created new prompt version: {new_version}")
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating new prompt version: {str(e)}")
            return None
    
    def activate_version(self, version: str) -> bool:
        """Activate a specific prompt version"""
        try:
            # Verify version exists
            prompt_version = self.get_prompt_version(version)
            if not prompt_version:
                logger.error(f"Cannot activate non-existent version: {version}")
                return False
            
            # Deactivate current version
            current_version = self.state.get("current_prompt_version")
            if current_version:
                self._update_version_status(current_version, "inactive")
            
            # Activate new version
            self._update_version_status(version, "active")
            self.state["current_prompt_version"] = version
            
            self._save_state()
            
            logger.info(f"Activated prompt version: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating version {version}: {str(e)}")
            return False
    
    def rollback_to_version(self, version: str) -> bool:
        """Rollback to a previous prompt version"""
        try:
            logger.info(f"Rolling back to version: {version}")
            
            # Verify version exists and was previously active
            prompt_version = self.get_prompt_version(version)
            if not prompt_version:
                logger.error(f"Cannot rollback to non-existent version: {version}")
                return False
            
            # Create rollback entry in history
            current_version = self.state.get("current_prompt_version")
            rollback_rationale = f"Rollback from {current_version} to {version}"
            
            # Activate the rollback version
            success = self.activate_version(version)
            
            if success:
                # Add rollback entry to history
                self.state["prompt_history"].append({
                    "version": version,
                    "timestamp": datetime.now().isoformat(),
                    "rationale": rollback_rationale,
                    "status": "rollback",
                    "previous_version": current_version
                })
                
                self._save_state()
                logger.info(f"Successfully rolled back to version: {version}")
            
            return success

        except Exception as e:
            logger.error(f"Error rolling back to version {version}: {str(e)}")
            return False

    def apply_improvements(self, improvement_ids: List[str]) -> Optional[str]:
        """Apply pending improvements to create a new prompt version"""
        try:
            # Get pending improvements
            pending_improvements = self.state.get("pending_improvements", [])

            # Filter improvements to apply
            improvements_to_apply = [
                imp for imp in pending_improvements
                if imp.get("id") in improvement_ids and imp.get("status") == "pending"
            ]

            if not improvements_to_apply:
                logger.warning("No valid pending improvements found to apply")
                return None

            # Aggregate changes from improvements
            aggregated_changes = {"prompt": {}}
            rationale_parts = []

            for improvement in improvements_to_apply:
                recommendation = improvement.get("recommendation", {})
                change = recommendation.get("change", "")
                rationale = recommendation.get("rationale", "")

                # Apply the change (this is simplified - in practice, you'd need more sophisticated merging)
                if "system_prompt" in change.lower():
                    # This is a system prompt change
                    current_prompt = self.get_current_prompt()
                    if current_prompt:
                        # Apply the change to system prompt
                        aggregated_changes["prompt"]["system_prompt"] = self._apply_prompt_change(
                            current_prompt.prompt.get("system_prompt", ""), change
                        )

                rationale_parts.append(f"- {rationale}: {change}")

                # Mark improvement as applied
                improvement["status"] = "applied"
                improvement["applied_date"] = datetime.now().isoformat()

            # Create new version
            current_version = self.state.get("current_prompt_version", "v1.0")
            combined_rationale = "Applied improvements:\n" + "\n".join(rationale_parts)

            new_version = self.create_new_version(
                current_version,
                aggregated_changes,
                combined_rationale
            )

            if new_version:
                self._save_state()
                logger.info(f"Applied {len(improvements_to_apply)} improvements to create version {new_version}")

            return new_version

        except Exception as e:
            logger.error(f"Error applying improvements: {str(e)}")
            return None

    def _apply_prompt_change(self, current_prompt: str, change_description: str) -> str:
        """Apply a change description to a prompt (simplified implementation)"""
        # This is a simplified implementation
        # In practice, you'd use more sophisticated NLP to apply changes

        if "empathetic" in change_description.lower():
            # Add empathetic language
            if "empathetic" not in current_prompt.lower():
                current_prompt += "\n\nAdditional guidance:\n- Use empathetic and understanding language\n- Acknowledge customer concerns with phrases like 'I understand' or 'That makes sense'"

        if "booking" in change_description.lower() and "improve" in change_description.lower():
            # Improve booking process
            if "booking process" not in current_prompt.lower():
                current_prompt += "\n\nBooking optimization:\n- Always confirm availability before proceeding\n- Clearly explain the booking process\n- Offer alternative times if preferred slot is unavailable"

        return current_prompt

    def _update_version_status(self, version: str, status: str):
        """Update the status of a prompt version"""
        try:
            prompt_file = os.path.join(self.prompts_dir, f"{version}.json")

            if os.path.exists(prompt_file):
                with open(prompt_file, 'r') as f:
                    prompt_data = json.load(f)

                prompt_data["status"] = status
                prompt_data["last_updated"] = datetime.now().isoformat()

                with open(prompt_file, 'w') as f:
                    json.dump(prompt_data, f, indent=2)

            # Update history
            for entry in self.state["prompt_history"]:
                if entry["version"] == version:
                    entry["status"] = status
                    break

        except Exception as e:
            logger.error(f"Error updating version status: {str(e)}")

    def _generate_version_number(self) -> str:
        """Generate a new version number"""
        try:
            # Get existing versions
            existing_versions = []
            for entry in self.state.get("prompt_history", []):
                version = entry.get("version", "")
                if version.startswith("v"):
                    try:
                        version_num = float(version[1:])
                        existing_versions.append(version_num)
                    except ValueError:
                        continue

            # Add current version
            current_version = self.state.get("current_prompt_version", "v1.0")
            if current_version.startswith("v"):
                try:
                    version_num = float(current_version[1:])
                    existing_versions.append(version_num)
                except ValueError:
                    pass

            # Generate next version
            if existing_versions:
                next_version = max(existing_versions) + 0.1
            else:
                next_version = 1.1

            return f"v{next_version:.1f}"

        except Exception as e:
            logger.error(f"Error generating version number: {str(e)}")
            return f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get the complete version history"""
        return self.state.get("prompt_history", [])

    def get_pending_improvements(self) -> List[Dict[str, Any]]:
        """Get all pending improvements"""
        return [
            imp for imp in self.state.get("pending_improvements", [])
            if imp.get("status") == "pending"
        ]

    def update_performance_metrics(self, version: str, metrics: Dict[str, float]) -> bool:
        """Update performance metrics for a prompt version"""
        try:
            prompt_file = os.path.join(self.prompts_dir, f"{version}.json")

            if not os.path.exists(prompt_file):
                logger.warning(f"Prompt version file not found: {prompt_file}")
                return False

            with open(prompt_file, 'r') as f:
                prompt_data = json.load(f)

            # Update metrics
            prompt_data["performance_metrics"].update(metrics)
            prompt_data["last_metrics_update"] = datetime.now().isoformat()

            with open(prompt_file, 'w') as f:
                json.dump(prompt_data, f, indent=2)

            logger.info(f"Updated performance metrics for version {version}")
            return True

        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
            return False


# Global prompt manager instance
prompt_manager = PromptManager()


# Convenience functions
def get_current_prompt() -> Optional[PromptVersion]:
    """Get the current active prompt"""
    return prompt_manager.get_current_prompt()


def get_system_prompt() -> str:
    """Get the current system prompt text"""
    current_prompt = get_current_prompt()
    if current_prompt and current_prompt.prompt:
        return current_prompt.prompt.get("system_prompt", "")
    return ""


def activate_prompt_version(version: str) -> bool:
    """Activate a specific prompt version"""
    return prompt_manager.activate_version(version)


def create_prompt_version(base_version: str, changes: Dict[str, Any], rationale: str) -> Optional[str]:
    """Create a new prompt version"""
    return prompt_manager.create_new_version(base_version, changes, rationale)


def apply_pending_improvements(improvement_ids: List[str]) -> Optional[str]:
    """Apply pending improvements"""
    return prompt_manager.apply_improvements(improvement_ids)


def rollback_prompt(version: str) -> bool:
    """Rollback to a previous prompt version"""
    return prompt_manager.rollback_to_version(version)
