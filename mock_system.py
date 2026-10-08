import json
import time

class MockDevOpsAPI:
    """
    Simulates a company's internal DevOps, Monitoring, and Ticketing APIs.
    Maintains state in memory to test the agent's ability to observe and verify.
    """
    def __init__(self):
        # Initial state: The billing_service is down due to a memory leak.
        self.services = {
            "billing_service": {"status": "degraded", "uptime": 120},
            "auth_service": {"status": "healthy", "uptime": 99940},
            "frontend_app": {"status": "healthy", "uptime": 45000}
        }
        
        self.active_alerts = [
            {"id": "ALT-992", "service": "billing_service", "message": "High latency and 500 errors detected", "severity": "HIGH"}
        ]
        
        self.tickets = []

    def get_alerts(self):
        """Simulates GET /api/v1/alerts"""
        return json.dumps({"status": "success", "alerts": self.active_alerts})

    def get_service_logs(self, service_name, lines=10):
        """Simulates GET /api/v1/services/{service_name}/logs"""
        if service_name not in self.services:
            return json.dumps({"error": f"Service '{service_name}' not found."})
        
        if service_name == "billing_service" and self.services[service_name]["status"] == "degraded":
            return json.dumps({
                "status": "success",
                "logs": [
                    "[INFO] Starting payment processing...",
                    "[WARN] Memory usage at 85%",
                    "[WARN] Memory usage at 95%",
                    "[ERROR] OutOfMemoryException: Heap space full. Process hanging.",
                    "[ERROR] Failed to serve request. Returning 500."
                ]
            })
        elif service_name == "billing_service" and self.services[service_name]["status"] == "healthy":
             return json.dumps({
                "status": "success",
                "logs": [
                    "[INFO] Service started successfully.",
                    "[INFO] Processing payment req_992...",
                    "[INFO] Payment req_992 successful. Returning 200 OK."
                ]
            })
        else:
            return json.dumps({"status": "success", "logs": ["[INFO] Standard operation normal."] * lines})

    def restart_service(self, service_name):
        """Simulates POST /api/v1/services/{service_name}/restart"""
        if service_name not in self.services:
            return json.dumps({"error": f"Service '{service_name}' not found."})
        
        # Simulate restart time
        time.sleep(1) 
        
        # Update state to healthy
        self.services[service_name]["status"] = "healthy"
        self.services[service_name]["uptime"] = 0
        
        # Clear related alerts
        self.active_alerts = [a for a in self.active_alerts if a["service"] != service_name]
        
        return json.dumps({"status": "success", "message": f"Service {service_name} successfully restarted."})

    def get_service_status(self, service_name):
        """Simulates GET /api/v1/services/{service_name}/status"""
        if service_name not in self.services:
             return json.dumps({"error": f"Service '{service_name}' not found."})
        
        return json.dumps({"status": "success", "data": self.services[service_name]})

    def create_ticket(self, title, description, severity):
        """Simulates POST /api/v1/tickets"""
        ticket_id = f"TICKET-{len(self.tickets) + 101}"
        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "severity": severity,
            "status": "OPEN"
        }
        self.tickets.append(ticket)
        return json.dumps({"status": "success", "ticket_id": ticket_id, "message": "Ticket successfully created."})

# Global singleton instance for our tools to use
system_mock = MockDevOpsAPI()
