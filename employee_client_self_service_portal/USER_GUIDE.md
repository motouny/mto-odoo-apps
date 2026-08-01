# User Guide

## Roles

| Who | Access |
|---|---|
| Employee (Portal user linked to an `hr.employee`) | My Profile, My Time Off, My Attendances, My Tasks, My Assignments, My Requests, Notifications |
| Portal Manager (a portal user set on a `project.project`) | My Team, Approvals, Team Tasks - scoped to that project's employees only |
| Client (new `group_ess_client`) | My Requests, Notifications - scoped to their own company's requests only |
| Request Manager (new `group_ess_request_manager`, internal) | Backend **Employee & Client Requests**: All Requests, My Tickets, Overdue, Configuration, Reports |

## Employee self-service

Log in and go to `/my`. Update contact details under **My Profile**,
submit and cancel leave under **My Time Off**, check in/out under **My
Attendances**, and see project tasks under **My Tasks** (read-only).

## Submitting a request

Go to **My Requests -> New Request**, pick a request type, priority and
subject, and submit. You'll see the request move through its status
history and can add comments or cancel it (while it's still open). Once a
request is closed, you can rate it 1-5.

## Portal Manager (project oversight)

If you've been set as a project's Portal Manager, you'll see a **My Team**
tile showing that project's employees and their status for today
(present / on leave / on permission / absent). **Approvals** lists pending
time-off requests for your team - approving here is a first-stage
approval; internal HR still finalizes it. **Team Tasks** lets you assign
lightweight tasks to your team and track them.

## Client self-service

If you've been given the **Client** group, logging in takes you straight
to **My Requests**, scoped to your own company. You can submit a new
service request, add comments, cancel while open, and rate it once closed.
You will never see another client's requests, or any employee data.

## Staff triage (backend)

Request Managers use the **Employee & Client Requests** app in the
backend. **All Requests** is the full queue; **My Tickets** filters to
what's assigned to you; **Overdue** flags anything past its due date.
Use the workflow buttons on a request (Start Review, Approve, Reject,
Request Info, Start Progress, Complete, Close) to move it forward - each
transition is recorded in the immutable **Status History** tab.

## Notifications

Every status change on your own request creates an in-portal notification
(visible under **Notifications**) and, if you have an email on file, an
email update as well.
