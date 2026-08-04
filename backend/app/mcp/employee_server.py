from mcp.server.fastmcp import FastMCP

from app.db.employee_db import get_employee_cursor

mcp = FastMCP("employee")


def _stringify(rows):
    for row in rows:
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                row[key] = value.isoformat()
    return rows


@mcp.tool()
def list_departments() -> list[dict]:
    """List every department with its id, name, and location."""
    with get_employee_cursor() as cursor:
        cursor.execute("SELECT * FROM departments ORDER BY department_name")
        return cursor.fetchall()


@mcp.tool()
def list_employees(department_name: str = None, status: str = None, limit: int = 50) -> list[dict]:
    """List employees, optionally filtered by department name and/or status
    (e.g. 'Active', 'Inactive'). Returns up to `limit` rows (default 50). For
    headcount/counting questions, use department_headcount instead of counting
    these rows yourself — this list may be truncated by `limit`."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.email, e.phone,
               e.designation, e.salary, e.hire_date, e.status,
               d.department_name, e.city, e.state, e.country
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        WHERE (%(department_name)s IS NULL OR d.department_name ILIKE %(department_name)s)
          AND (%(status)s IS NULL OR e.status ILIKE %(status)s)
        ORDER BY e.employee_id
        LIMIT %(limit)s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(
            query,
            {"department_name": department_name, "status": status, "limit": limit},
        )
        return _stringify(cursor.fetchall())


@mcp.tool()
def get_employee(employee_id: int) -> dict:
    """Get full details for a single employee by id, including department
    name and manager's name. Returns an empty dict if not found."""
    query = """
        SELECT e.*, d.department_name,
               m.first_name AS manager_first_name, m.last_name AS manager_last_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        LEFT JOIN employees m ON m.employee_id = e.manager_id
        WHERE e.employee_id = %s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (employee_id,))
        row = cursor.fetchone()
        return _stringify([row])[0] if row else {}


@mcp.tool()
def search_employees(query: str) -> list[dict]:
    """Search employees by first name, last name, email, or designation
    (case-insensitive partial match). Returns up to 50 matches."""
    like = f"%{query}%"
    sql = """
        SELECT e.employee_id, e.first_name, e.last_name, e.email,
               e.designation, e.status, d.department_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        WHERE e.first_name ILIKE %s OR e.last_name ILIKE %s
           OR e.email ILIKE %s OR e.designation ILIKE %s
        LIMIT 50
    """
    with get_employee_cursor() as cursor:
        cursor.execute(sql, (like, like, like, like))
        return _stringify(cursor.fetchall())


@mcp.tool()
def department_headcount() -> list[dict]:
    """Exact employee count per department, computed in SQL. Always use this
    tool (not list_employees) to answer any 'how many employees in <dept>'
    or headcount-style question."""
    query = """
        SELECT d.department_name, COUNT(e.employee_id) AS headcount
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.department_id
        GROUP BY d.department_name
        ORDER BY headcount DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


@mcp.tool()
def get_attendance(employee_id: int, start_date: str = None, end_date: str = None) -> list[dict]:
    """Get attendance records for an employee, optionally bounded by
    start_date/end_date (YYYY-MM-DD). Returns up to 100 rows, most recent first."""
    query = """
        SELECT attendance_date, check_in, check_out, status
        FROM attendance
        WHERE employee_id = %(employee_id)s
          AND (%(start_date)s::date IS NULL OR attendance_date >= %(start_date)s::date)
          AND (%(end_date)s::date IS NULL OR attendance_date <= %(end_date)s::date)
        ORDER BY attendance_date DESC
        LIMIT 100
    """
    with get_employee_cursor() as cursor:
        cursor.execute(
            query,
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        return _stringify(cursor.fetchall())


@mcp.tool()
def get_leave_requests(employee_id: int, status: str = None) -> list[dict]:
    """Get leave requests for an employee, optionally filtered by status
    (e.g. 'Approved', 'Pending', 'Rejected')."""
    query = """
        SELECT leave_id, leave_type, start_date, end_date, reason, status
        FROM leave_requests
        WHERE employee_id = %(employee_id)s
          AND (%(status)s IS NULL OR status ILIKE %(status)s)
        ORDER BY start_date DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, {"employee_id": employee_id, "status": status})
        return _stringify(cursor.fetchall())


@mcp.tool()
def get_payroll(employee_id: int, limit: int = 12) -> list[dict]:
    """Get payroll history for an employee, most recent first (default last 12 records)."""
    query = """
        SELECT pay_month, basic_salary, bonus, deductions, net_salary, payment_date
        FROM payroll
        WHERE employee_id = %s
        ORDER BY pay_month DESC
        LIMIT %s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (employee_id, limit))
        return _stringify(cursor.fetchall())


@mcp.tool()
def list_projects() -> list[dict]:
    """List all projects with client name and start/end dates."""
    with get_employee_cursor() as cursor:
        cursor.execute("SELECT * FROM projects ORDER BY start_date DESC")
        return _stringify(cursor.fetchall())


@mcp.tool()
def get_employee_projects(employee_id: int) -> list[dict]:
    """List the projects a given employee is/was assigned to."""
    query = """
        SELECT p.project_id, p.project_name, p.client_name, p.start_date, p.end_date,
               ep.assigned_date
        FROM employee_projects ep
        JOIN projects p ON p.project_id = ep.project_id
        WHERE ep.employee_id = %s
        ORDER BY ep.assigned_date DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (employee_id,))
        return _stringify(cursor.fetchall())


@mcp.tool()
def salary_stats_by_department() -> list[dict]:
    """Average, minimum, and maximum salary per department."""
    query = """
        SELECT d.department_name,
               ROUND(AVG(e.salary), 2) AS avg_salary,
               MIN(e.salary) AS min_salary,
               MAX(e.salary) AS max_salary
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.department_id
        GROUP BY d.department_name
        ORDER BY avg_salary DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query)
        return _stringify(cursor.fetchall())


@mcp.tool()
def top_earners(limit: int = 10) -> list[dict]:
    """List the highest-paid employees company-wide, descending by salary."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.designation,
               e.salary, d.department_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        ORDER BY e.salary DESC
        LIMIT %s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (limit,))
        return _stringify(cursor.fetchall())


@mcp.tool()
def total_payroll_cost(pay_month: str) -> dict:
    """Total payroll cost across the whole company for a given month.
    `pay_month` must be in 'YYYY-MM' format, e.g. '2026-07'."""
    query = """
        SELECT COUNT(*) AS employee_count,
               SUM(basic_salary) AS total_basic_salary,
               SUM(bonus) AS total_bonus,
               SUM(deductions) AS total_deductions,
               SUM(net_salary) AS total_net_salary
        FROM payroll
        WHERE to_char(pay_month, 'YYYY-MM') = %s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (pay_month,))
        row = cursor.fetchone()
        return _stringify([row])[0] if row else {}


@mcp.tool()
def get_direct_reports(manager_id: int) -> list[dict]:
    """List employees who report directly to the given manager (by employee id)."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.designation,
               d.department_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        WHERE e.manager_id = %s
        ORDER BY e.employee_id
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (manager_id,))
        return _stringify(cursor.fetchall())


@mcp.tool()
def get_manager(employee_id: int) -> dict:
    """Get the manager's details for a given employee. Returns an empty
    dict if the employee has no manager on record."""
    query = """
        SELECT m.employee_id, m.first_name, m.last_name, m.designation, m.email
        FROM employees e
        JOIN employees m ON m.employee_id = e.manager_id
        WHERE e.employee_id = %s
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (employee_id,))
        row = cursor.fetchone()
        return _stringify([row])[0] if row else {}


@mcp.tool()
def attendance_summary(employee_id: int, start_date: str = None, end_date: str = None) -> dict:
    """Attendance status breakdown (e.g. Present/Absent/Leave counts) and
    attendance rate for an employee, optionally bounded by start_date/end_date
    (YYYY-MM-DD)."""
    query = """
        SELECT status, COUNT(*) AS count
        FROM attendance
        WHERE employee_id = %(employee_id)s
          AND (%(start_date)s::date IS NULL OR attendance_date >= %(start_date)s::date)
          AND (%(end_date)s::date IS NULL OR attendance_date <= %(end_date)s::date)
        GROUP BY status
    """
    with get_employee_cursor() as cursor:
        cursor.execute(
            query,
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        breakdown = cursor.fetchall()

    total = sum(row["count"] for row in breakdown)
    present = sum(row["count"] for row in breakdown if row["status"] == "Present")
    rate = round(present / total * 100, 1) if total else None

    return {
        "employee_id": employee_id,
        "total_days": total,
        "breakdown": breakdown,
        "attendance_rate_percent": rate,
    }


@mcp.tool()
def leave_balance(employee_id: int) -> list[dict]:
    """Leave usage summary for an employee: request count and total days
    per leave_type/status combination."""
    query = """
        SELECT leave_type, status,
               COUNT(*) AS request_count,
               SUM(GREATEST(end_date - start_date + 1, 0)) AS total_days
        FROM leave_requests
        WHERE employee_id = %s
        GROUP BY leave_type, status
        ORDER BY leave_type, status
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (employee_id,))
        return cursor.fetchall()


@mcp.tool()
def employees_on_leave(date: str = None) -> list[dict]:
    """List employees on approved leave for a given date (YYYY-MM-DD),
    defaulting to today if not specified."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name,
               lr.leave_type, lr.start_date, lr.end_date
        FROM leave_requests lr
        JOIN employees e ON e.employee_id = lr.employee_id
        WHERE lr.status = 'Approved'
          AND COALESCE(%(date)s::date, CURRENT_DATE) BETWEEN lr.start_date AND lr.end_date
        ORDER BY e.employee_id
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, {"date": date})
        return _stringify(cursor.fetchall())


@mcp.tool()
def recent_hires(days: int = 30) -> list[dict]:
    """List employees hired within the last `days` days (default 30), most recent first."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.designation,
               e.hire_date, d.department_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id = e.department_id
        WHERE e.hire_date >= CURRENT_DATE - (%s || ' days')::interval
        ORDER BY e.hire_date DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (days,))
        return _stringify(cursor.fetchall())


@mcp.tool()
def project_staffing(project_id: int) -> list[dict]:
    """List employees assigned to a given project, with their designation
    and assignment date."""
    query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.designation,
               ep.assigned_date
        FROM employee_projects ep
        JOIN employees e ON e.employee_id = ep.employee_id
        WHERE ep.project_id = %s
        ORDER BY ep.assigned_date
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query, (project_id,))
        return _stringify(cursor.fetchall())


@mcp.tool()
def active_projects() -> list[dict]:
    """List projects that are currently active (end_date is in the future or unset)."""
    query = """
        SELECT * FROM projects
        WHERE end_date IS NULL OR end_date >= CURRENT_DATE
        ORDER BY start_date DESC
    """
    with get_employee_cursor() as cursor:
        cursor.execute(query)
        return _stringify(cursor.fetchall())


if __name__ == "__main__":
    mcp.run()
