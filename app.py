import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import String, Integer, select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------
# DATABASE CONFIGURATION (Async SQLite with WAL Mode)
# ---------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///sprintsync.db"

class Base(DeclarativeBase):
    pass

class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Backlog")  # Backlog, Active Dev, Completed
    priority: Mapped[str] = mapped_column(String(20), default="Medium")  # High, Medium, Low
    story_points: Mapped[int] = mapped_column(Integer, default=1)
    assignee_initials: Mapped[str] = mapped_column(String(4), default="DEV")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        # Enable Write-Ahead Logging (WAL) for rapid non-blocking operations
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed initial demo tasks if the database is completely empty
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(TaskModel))
            if not result.scalars().first():
                demo_tasks = [
                    TaskModel(
                        title="Configure OAuth2 Authentication", 
                        description="Implement JWT authentication tokens and secure TLS connections across microservices.",
                        status="Backlog", 
                        priority="High", 
                        story_points=5, 
                        assignee_initials="AX"
                    ),
                    TaskModel(
                        title="Optimize Database Query Performance", 
                        description="Refactor database indices and isolate slow-running analytical operations.",
                        status="Active Dev", 
                        priority="Medium", 
                        story_points=3, 
                        assignee_initials="JD"
                    ),
                    TaskModel(
                        title="Deploy Project Dashboard Dashboard UI", 
                        description="Publish the core responsive terminal user interface to production environments.",
                        status="Completed", 
                        priority="Low", 
                        story_points=2, 
                        assignee_initials="CY"
                    )
                ]
                session.add_all(demo_tasks)

# ---------------------------------------------------------
# PYDANTIC SCHEMAS
# ---------------------------------------------------------
class TaskSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    status: str
    priority: str
    story_points: int
    assignee_initials: str

    class Config:
        from_attributes = True

class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)
    status: str = Field("Backlog", pattern="^(Backlog|Active Dev|Completed)$")
    priority: str = Field("Medium", pattern="^(High|Medium|Low)$")
    story_points: int = Field(1, ge=1, le=13)
    assignee_initials: str = Field("DEV", min_length=1, max_length=4)

class TaskStatusUpdateSchema(BaseModel):
    status: str = Field(..., pattern="^(Backlog|Active Dev|Completed)$")

# ---------------------------------------------------------
# FASTAPI APP & LIFE-CYCLE
# ---------------------------------------------------------
app = FastAPI(title="SprintSync Dashboard")

@app.on_event("startup")
async def startup_event():
    await init_db()

# ---------------------------------------------------------
# API ROUTER & ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/tasks", response_model=List[TaskSchema])
async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(TaskModel).order_by(TaskModel.id.asc()))
        tasks = result.scalars().all()
        return tasks

@app.post("/api/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreateSchema):
    async with async_session() as session:
        async with session.begin():
            new_task = TaskModel(
                title=payload.title,
                description=payload.description,
                status=payload.status,
                priority=payload.priority,
                story_points=payload.story_points,
                assignee_initials=payload.assignee_initials.upper()
            )
            session.add(new_task)
        await session.refresh(new_task)
        return new_task

@app.patch("/api/tasks/{task_id}/status", response_model=TaskSchema)
async def update_task_status(task_id: int, payload: TaskStatusUpdateSchema):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(TaskModel).where(TaskModel.id == task_id))
            task = result.scalars().first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task.status = payload.status
            session.add(task)
        await session.refresh(task)
        return task

@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(TaskModel).where(TaskModel.id == task_id))
            task = result.scalars().first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            await session.delete(task)
    return HTMLResponse(status_code=204)

# ---------------------------------------------------------
# FRONTEND HTML CORE (Dark UI Theme with Standard English)
# ---------------------------------------------------------
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SprintSync // Project Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        cyber: {
                            black: '#030712',
                            grayDark: '#0b0f19',
                            grayMedium: '#111827',
                            grayLight: '#1f2937',
                            neonCyan: '#06b6d4',
                            neonPurple: '#a855f7',
                            neonMagenta: '#ec4899',
                            neonGreen: '#10b981',
                        }
                    },
                    boxShadow: {
                        'neon-cyan': '0 0 10px rgba(6, 182, 212, 0.5), 0 0 2px rgba(6, 182, 212, 0.3)',
                        'neon-purple': '0 0 10px rgba(168, 85, 247, 0.5), 0 0 2px rgba(168, 85, 247, 0.3)',
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;700&display=swap');
        body {
            font-family: 'Fira Code', monospace;
        }
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0f19;
        }
        ::-webkit-scrollbar-thumb {
            background: #1f2937;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #06b6d4;
        }
    </style>
</head>
<body class="h-full text-slate-100 flex flex-col bg-cyber-black selection:bg-cyber-neonPurple selection:text-white">

    <header class="border-b border-cyber-neonCyan/30 bg-cyber-grayDark/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center space-x-3">
            <div class="h-4 w-4 rounded-full bg-cyber-neonCyan animate-pulse shadow-neon-cyan"></div>
            <div>
                <h1 class="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyber-neonCyan to-cyber-neonPurple">
                    SPRINTSYNC // MANAGEMENT
                </h1>
                <p class="text-xs text-slate-500 uppercase">Interactive Sprint & Kanban Board</p>
            </div>
        </div>

        <div class="flex items-center space-x-6 bg-cyber-grayMedium border border-slate-800 rounded px-4 py-2 w-full sm:w-auto">
            <div class="text-xs">
                <span class="text-slate-500 uppercase block">Total Points</span>
                <span id="telemetry-total" class="text-base font-bold text-cyber-neonCyan">0</span>
            </div>
            <div class="h-8 w-[1px] bg-slate-800"></div>
            <div class="text-xs">
                <span class="text-slate-500 uppercase block">Completed Points</span>
                <span id="telemetry-completed" class="text-base font-bold text-cyber-neonGreen">0</span>
            </div>
            <div class="h-8 w-[1px] bg-slate-800"></div>
            <div class="flex-1 sm:w-48">
                <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                    <span>SPRINT VELOCITY</span>
                    <span id="telemetry-percentage">0%</span>
                </div>
                <div class="w-full bg-slate-900 h-1.5 rounded overflow-hidden border border-slate-800">
                    <div id="telemetry-progress" class="bg-gradient-to-r from-cyber-neonCyan to-cyber-neonPurple h-full transition-all duration-500 ease-out" style="width: 0%"></div>
                </div>
            </div>
        </div>

        <button onclick="toggleModal(true)" class="bg-gradient-to-r from-cyber-neonCyan to-cyber-neonPurple hover:from-cyber-neonCyan/80 hover:to-cyber-neonPurple/80 text-cyber-black font-semibold text-xs py-2 px-4 rounded shadow-neon-cyan transition-all duration-300 transform active:scale-95 flex items-center gap-1.5">
            <span>+</span> CREATE TASK
        </button>
    </header>

    <main class="flex-1 p-6 overflow-x-auto">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-w-[900px] items-start">
            
            <div class="bg-cyber-grayDark/50 border border-slate-800 rounded-lg p-4 flex flex-col h-[calc(100vh-180px)] min-h-[450px]">
                <div class="flex justify-between items-center pb-3 border-b border-slate-800 mb-4">
                    <div class="flex items-center space-x-2">
                        <span class="h-2 w-2 rounded-full bg-slate-400"></span>
                        <h2 class="text-sm font-semibold tracking-widest text-slate-300 uppercase">BACKLOG</h2>
                    </div>
                    <span id="count-backlog" class="text-xs font-bold text-slate-500 border border-slate-800 rounded px-2 py-0.5">0</span>
                </div>
                <div id="col-backlog" 
                     class="flex-1 overflow-y-auto space-y-3 transition-colors duration-200" 
                     ondragover="allowDrop(event)" 
                     ondrop="drop(event, 'Backlog')"
                     ondragenter="highlightColumn('col-backlog')"
                     ondragleave="unhighlightColumn('col-backlog')">
                </div>
            </div>

            <div class="bg-cyber-grayDark/50 border border-slate-800 rounded-lg p-4 flex flex-col h-[calc(100vh-180px)] min-h-[450px]">
                <div class="flex justify-between items-center pb-3 border-b border-slate-800 mb-4">
                    <div class="flex items-center space-x-2">
                        <span class="h-2 w-2 rounded-full bg-cyber-neonCyan animate-pulse"></span>
                        <h2 class="text-sm font-semibold tracking-widest text-cyber-neonCyan uppercase">ACTIVE DEV</h2>
                    </div>
                    <span id="count-active" class="text-xs font-bold text-cyber-neonCyan border border-cyber-neonCyan/30 rounded px-2 py-0.5">0</span>
                </div>
                <div id="col-active" 
                     class="flex-1 overflow-y-auto space-y-3 transition-colors duration-200" 
                     ondragover="allowDrop(event)" 
                     ondrop="drop(event, 'Active Dev')"
                     ondragenter="highlightColumn('col-active')"
                     ondragleave="unhighlightColumn('col-active')">
                </div>
            </div>

            <div class="bg-cyber-grayDark/50 border border-slate-800 rounded-lg p-4 flex flex-col h-[calc(100vh-180px)] min-h-[450px]">
                <div class="flex justify-between items-center pb-3 border-b border-slate-800 mb-4">
                    <div class="flex items-center space-x-2">
                        <span class="h-2 w-2 rounded-full bg-cyber-neonGreen"></span>
                        <h2 class="text-sm font-semibold tracking-widest text-cyber-neonGreen uppercase">QA / COMPLETED</h2>
                    </div>
                    <span id="count-completed" class="text-xs font-bold text-cyber-neonGreen border border-cyber-neonGreen/30 rounded px-2 py-0.5">0</span>
                </div>
                <div id="col-completed" 
                     class="flex-1 overflow-y-auto space-y-3 transition-colors duration-200" 
                     ondragover="allowDrop(event)" 
                     ondrop="drop(event, 'Completed')"
                     ondragenter="highlightColumn('col-completed')"
                     ondragleave="unhighlightColumn('col-completed')">
                </div>
            </div>

        </div>
    </main>

    <div id="task-modal" class="hidden fixed inset-0 z-50 overflow-y-auto bg-cyber-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-cyber-grayDark border border-cyber-neonCyan/40 rounded-lg shadow-neon-purple max-w-md w-full p-6 relative">
            <div class="absolute top-4 right-4">
                <button onclick="toggleModal(false)" class="text-slate-500 hover:text-cyber-neonMagenta text-xl transition-colors">&times;</button>
            </div>
            <h3 class="text-base font-bold text-cyber-neonCyan mb-4 border-b border-slate-800 pb-2">CREATE NEW TASK</h3>
            <form id="task-form" onsubmit="handleFormSubmit(event)">
                <div class="mb-4">
                    <label class="block text-xs uppercase text-slate-400 mb-1">Task Title *</label>
                    <input type="text" id="form-title" required class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all" placeholder="E.g., Integrate Service Engine">
                </div>
                <div class="mb-4">
                    <label class="block text-xs uppercase text-slate-400 mb-1">Description</label>
                    <textarea id="form-description" rows="3" class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all" placeholder="Provide system configurations..."></textarea>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Priority</label>
                        <select id="form-priority" class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all">
                            <option value="Low">Low</option>
                            <option value="Medium" selected>Medium</option>
                            <option value="High">High</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Story Points</label>
                        <select id="form-points" class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all">
                            <option value="1">1 pt</option>
                            <option value="2">2 pts</option>
                            <option value="3" selected>3 pts</option>
                            <option value="5">5 pts</option>
                            <option value="8">8 pts</option>
                            <option value="13">13 pts</option>
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Assignee Initials</label>
                        <input type="text" id="form-assignee" maxlength="4" value="DEV" class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all uppercase">
                    </div>
                    <div>
                        <label class="block text-xs uppercase text-slate-400 mb-1">Initial Status</label>
                        <select id="form-status" class="w-full bg-cyber-grayMedium border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyber-neonCyan transition-all">
                            <option value="Backlog" selected>Backlog</option>
                            <option value="Active Dev">Active Dev</option>
                            <option value="Completed">Completed</option>
                        </select>
                    </div>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" onclick="toggleModal(false)" class="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs py-2 px-4 rounded transition-all">CANCEL</button>
                    <button type="submit" class="bg-gradient-to-r from-cyber-neonCyan to-cyber-neonPurple hover:from-cyber-neonCyan/85 hover:to-cyber-neonPurple/85 text-cyber-black font-semibold text-xs py-2 px-4 rounded shadow-neon-cyan transition-all">CREATE</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let allTasks = [];

        // Fetch tasks and render on page load
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                if (!response.ok) throw new Error("Could not fetch database records.");
                allTasks = await response.json();
                renderBoard();
            } catch (err) {
                console.error("Connection failure:", err);
            }
        }

        // Render board layout dynamic cards & calculate telemetry values
        function renderBoard() {
            const colBacklog = document.getElementById('col-backlog');
            const colActive = document.getElementById('col-active');
            const colCompleted = document.getElementById('col-completed');

            // Reset Columns
            colBacklog.innerHTML = '';
            colActive.innerHTML = '';
            colCompleted.innerHTML = '';

            let counts = { 'Backlog': 0, 'Active Dev': 0, 'Completed': 0 };
            let totalStoryPoints = 0;
            let completedStoryPoints = 0;

            allTasks.forEach(task => {
                totalStoryPoints += task.story_points;
                if (task.status === 'Completed') {
                    completedStoryPoints += task.story_points;
                }

                const card = createTaskCard(task);
                if (task.status === 'Backlog') {
                    colBacklog.appendChild(card);
                    counts['Backlog']++;
                } else if (task.status === 'Active Dev') {
                    colActive.appendChild(card);
                    counts['Active Dev']++;
                } else {
                    colCompleted.appendChild(card);
                    counts['Completed']++;
                }
            });

            // Update DOM Counts
            document.getElementById('count-backlog').innerText = counts['Backlog'];
            document.getElementById('count-active').innerText = counts['Active Dev'];
            document.getElementById('count-completed').innerText = counts['Completed'];

            // Update Telemetry Header
            document.getElementById('telemetry-total').innerText = totalStoryPoints;
            document.getElementById('telemetry-completed').innerText = completedStoryPoints;
            
            const progressPercentage = totalStoryPoints > 0 ? Math.round((completedStoryPoints / totalStoryPoints) * 100) : 0;
            document.getElementById('telemetry-percentage').innerText = progressPercentage + '%';
            document.getElementById('telemetry-progress').style.width = progressPercentage + '%';
        }

        // Create individual card elements
        function createTaskCard(task) {
            const card = document.createElement('div');
            card.id = `task-${task.id}`;
            card.className = "bg-cyber-grayMedium border border-slate-800 hover:border-cyber-neonCyan/40 p-4 rounded shadow-md cursor-grab active:cursor-grabbing transition-all duration-300 relative group";
            card.draggable = true;
            card.ondragstart = (e) => drag(e, task.id);

            // Priority styling map
            const priorityColors = {
                'High': 'bg-cyber-neonMagenta/20 text-cyber-neonMagenta border-cyber-neonMagenta/40',
                'Medium': 'bg-cyber-neonPurple/20 text-cyber-neonPurple border-cyber-neonPurple/40',
                'Low': 'bg-cyber-neonCyan/20 text-cyber-neonCyan border-cyber-neonCyan/40'
            };
            const priorityClass = priorityColors[task.priority] || priorityColors['Medium'];

            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${priorityClass}">
                        ${task.priority}
                    </span>
                    <button onclick="deleteTask(${task.id})" class="text-slate-600 hover:text-cyber-neonMagenta opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-xs">
                        &times; DELETE
                    </button>
                </div>
                <h4 class="text-xs font-bold text-slate-200 mb-1 group-hover:text-cyber-neonCyan transition-colors duration-200">${task.title}</h4>
                <p class="text-[11px] text-slate-400 line-clamp-2 mb-4 leading-relaxed">${task.description || 'No additional details provided.'}</p>
                <div class="flex justify-between items-center border-t border-slate-800/60 pt-3">
                    <div class="flex items-center space-x-1">
                        <span class="text-[10px] text-slate-500 uppercase">Weight:</span>
                        <span class="text-xs font-bold text-slate-300">${task.story_points} SP</span>
                    </div>
                    <div class="h-6 w-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-cyber-neonCyan" title="Assignee: ${task.assignee_initials}">
                        ${task.assignee_initials}
                    </div>
                </div>
            `;
            return card;
        }

        // Native Drag-and-Drop Operations
        function drag(event, taskId) {
            event.dataTransfer.setData("text/plain", taskId);
            // Dynamic slight visual dim when dragging
            setTimeout(() => {
                document.getElementById(`task-${taskId}`).classList.add('opacity-40');
            }, 0);
        }

        document.addEventListener('dragend', (event) => {
            const opacityCards = document.querySelectorAll('.opacity-40');
            opacityCards.forEach(card => card.classList.remove('opacity-40'));
        });

        function allowDrop(event) {
            event.preventDefault();
        }

        function highlightColumn(colId) {
            document.getElementById(colId).classList.add('bg-cyber-neonCyan/5');
        }

        function unhighlightColumn(colId) {
            document.getElementById(colId).classList.remove('bg-cyber-neonCyan/5');
        }

        async function drop(event, targetStatus) {
            event.preventDefault();
            const taskIdStr = event.dataTransfer.getData("text/plain");
            const taskId = parseInt(taskIdStr, 10);
            
            // Remove highlight states
            document.getElementById('col-backlog').classList.remove('bg-cyber-neonCyan/5');
            document.getElementById('col-active').classList.remove('bg-cyber-neonCyan/5');
            document.getElementById('col-completed').classList.remove('bg-cyber-neonCyan/5');

            if (!taskId) return;

            // Optimistic Client update
            const originalTasks = [...allTasks];
            const taskIndex = allTasks.findIndex(t => t.id === taskId);
            if (taskIndex > -1 && allTasks[taskIndex].status !== targetStatus) {
                allTasks[taskIndex].status = targetStatus;
                renderBoard();

                // Fire persistence update to backend
                try {
                    const response = await fetch(`/api/tasks/${taskId}/status`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: targetStatus })
                    });
                    if (!response.ok) throw new Error("Synchronization failure.");
                    
                    const updatedTask = await response.json();
                    allTasks[taskIndex] = updatedTask; // Sync updated state from backend
                } catch (err) {
                    console.error("Rolling back state transition due to server error:", err);
                    allTasks = originalTasks; // Rollback UI if failed
                    renderBoard();
                }
            } else {
                const targetCard = document.getElementById(`task-${taskId}`);
                if (targetCard) targetCard.classList.remove('opacity-40');
            }
        }

        // Delete Task Pipeline
        async function deleteTask(taskId) {
            const confirmed = confirm("Are you sure you want to permanently delete this task?");
            if (!confirmed) return;

            try {
                const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
                if (!response.ok) throw new Error("Delete operations failed.");
                
                allTasks = allTasks.filter(t => t.id !== taskId);
                renderBoard();
            } catch (err) {
                console.error(err);
                alert("Failed to delete task.");
            }
        }

        // Modal Controls
        function toggleModal(show) {
            const modal = document.getElementById('task-modal');
            if (show) {
                modal.classList.remove('hidden');
                document.getElementById('form-title').focus();
            } else {
                modal.classList.add('hidden');
                document.getElementById('task-form').reset();
            }
        }

        // Task Creation Form Execution
        async function handleFormSubmit(event) {
            event.preventDefault();

            const title = document.getElementById('form-title').value;
            const description = document.getElementById('form-description').value;
            const priority = document.getElementById('form-priority').value;
            const story_points = parseInt(document.getElementById('form-points').value, 10);
            const assignee_initials = document.getElementById('form-assignee').value || 'DEV';
            const status = document.getElementById('form-status').value;

            try {
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        description,
                        priority,
                        story_points,
                        assignee_initials,
                        status
                    })
                });

                if (!response.ok) throw new Error("Failed to insert task.");
                const newTask = await response.json();
                
                allTasks.push(newTask);
                toggleModal(false);
                renderBoard();
            } catch (err) {
                console.error(err);
                alert("Creation validation error. Please check your data parameters.");
            }
        }

        // Initial loading setup
        window.addEventListener('DOMContentLoaded', loadTasks);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTMLResponse(content=HTML_CONTENT, status_code=200)

# ---------------------------------------------------------
# RUNNER CONFIGURATION
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
