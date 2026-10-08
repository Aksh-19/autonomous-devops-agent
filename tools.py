from mock_system import system_mock

def get_active_alerts():
    """Returns a JSON string of all currently active system alerts."""
    return system_mock.get_alerts()

def get_service_logs(service_name: str):
    """
    Returns a JSON string containing the recent logs for a given service.
    Use this to diagnose WHY a service might be degraded.
    """
    return system_mock.get_service_logs(service_name)

def restart_service(service_name: str):
    """
    Restarts a specific service by name. 
    Returns a JSON string indicating success or failure.
    """
    return system_mock.restart_service(service_name)

def get_service_status(service_name: str):
    """
    Gets the current health status and uptime of a service.
    Use this to VERIFY if a remediation action (like a restart) actually worked.
    """
    return system_mock.get_service_status(service_name)

def create_incident_ticket(title: str, description: str, severity: str):
    """
    Creates a Jira-like incident ticket. 
    Returns a JSON string with the ticket ID.
    Use this to document issues AFTER you have resolved them.
    """
    return system_mock.create_ticket(title, description, severity)
