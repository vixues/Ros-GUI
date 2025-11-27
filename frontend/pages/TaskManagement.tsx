
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { Task, TaskStatus, TaskPriority } from '../types';
import { Plus, Trash2, Clock, AlertCircle, X, CheckCircle, Activity, GripVertical, Calendar } from 'lucide-react';
import { cn } from '../lib/utils';

// Flat modern priority badges
const PriorityBadge = ({ priority }: { priority: TaskPriority }) => {
  const styles = {
    [TaskPriority.LOW]: 'bg-zinc-800 text-zinc-400',
    [TaskPriority.MEDIUM]: 'bg-blue-500/20 text-blue-400',
    [TaskPriority.HIGH]: 'bg-amber-500/20 text-amber-400',
    [TaskPriority.CRITICAL]: 'bg-red-500/20 text-red-400',
  };
  return (
    <span className={cn("text-[9px] px-2 py-0.5 rounded font-bold uppercase tracking-wider", styles[priority])}>
      {priority}
    </span>
  );
};

export const TaskManagement: React.FC = () => {
  const { tasks, fetchTasks, updateTaskLocally, addTaskLocally, drones, fetchDrones } = useStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [draggedTaskId, setDraggedTaskId] = useState<number | null>(null);

  // Form State
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);
  const [selectedDrones, setSelectedDrones] = useState<number[]>([]);

  useEffect(() => {
    fetchTasks();
    if (drones.length === 0) fetchDrones();
  }, [fetchTasks, fetchDrones, drones.length]);

  const handleCreateTask = async () => {
    if (!newTaskTitle) return;

    const newTaskPartial: Partial<Task> = {
      title: newTaskTitle,
      description: newTaskDesc,
      priority: newTaskPriority,
      status: TaskStatus.PENDING,
      assigned_drone_ids: selectedDrones
    };

    try {
      const createdTask = await api.createTask(newTaskPartial);
      addTaskLocally(createdTask);
      setIsModalOpen(false);
      resetForm();
    } catch (err) {
      console.error("Error creating task", err);
    }
  };

  const updateStatus = async (task: Task, newStatus: TaskStatus) => {
    const updated = { ...task, status: newStatus };
    updateTaskLocally(updated);
    try {
      await api.updateTask(task.id, { status: newStatus });
    } catch(e) { console.warn("Update failed on backend"); }
  };

  const resetForm = () => {
    setNewTaskTitle('');
    setNewTaskDesc('');
    setNewTaskPriority(TaskPriority.MEDIUM);
    setSelectedDrones([]);
  };

  const toggleDroneSelection = (id: number) => {
    setSelectedDrones(prev => 
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  };

  // DnD Handlers
  const handleDragStart = (e: React.DragEvent, taskId: number) => {
    setDraggedTaskId(taskId);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", taskId.toString());
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    if (draggedTaskId) {
      const task = tasks.find(t => t.id === draggedTaskId);
      if (task && task.status !== status) {
        updateStatus(task, status);
      }
    }
    setDraggedTaskId(null);
  };

  const TaskCard = ({ task }: { task: Task }) => {
    const isDragging = draggedTaskId === task.id;
    return (
      <div 
        draggable
        onDragStart={(e) => handleDragStart(e, task.id)}
        className={cn(
          "bg-surface p-4 mb-3 rounded-lg shadow-sm border border-zinc-800/50 transition-all group relative cursor-grab active:cursor-grabbing hover:border-zinc-700 hover:shadow-md",
          isDragging && 'opacity-50 ring-2 ring-white/20'
        )}
      >
         <div className="flex justify-between items-start mb-3">
           <PriorityBadge priority={task.priority} />
           <GripVertical size={14} className="text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity" />
         </div>
         
         <h3 className="text-white font-bold text-sm mb-1 leading-tight">{task.title}</h3>
         <p className="text-zinc-500 text-xs mb-4 line-clamp-2">{task.description || "No description provided."}</p>
         
         <div className="flex items-center justify-between pt-3 border-t border-zinc-800/50">
            <div className="flex -space-x-1.5 overflow-hidden">
              {task.assigned_drone_ids.length > 0 ? (
                 task.assigned_drone_ids.map(id => (
                   <div key={id} className="w-6 h-6 rounded-full bg-zinc-800 border-2 border-surface flex items-center justify-center text-[9px] text-zinc-300 font-bold ring-1 ring-zinc-700">
                      {id}
                   </div>
                 ))
              ) : (
                  <span className="text-[10px] text-zinc-600 font-medium italic">Unassigned</span>
              )}
            </div>
            <div className="flex items-center gap-1 text-[10px] text-zinc-500">
               <Calendar size={10} />
               <span>Today</span>
            </div>
         </div>
      </div>
    );
  };

  const Column = ({ status, title, icon: Icon, count }: any) => (
    <div 
      onDragOver={handleDragOver}
      onDrop={(e) => handleDrop(e, status)}
      className={cn(
        "flex flex-col bg-surface_highlight/20 rounded-xl p-4 transition-all duration-300 border border-transparent h-full",
        draggedTaskId && 'bg-surface_highlight/40 border-dashed border-zinc-700'
      )}
    >
       <div className="flex items-center gap-2 mb-4 pb-2">
          <Icon size={16} className="text-zinc-500" />
          <span className="font-bold text-sm text-zinc-300">{title}</span>
          <span className="ml-auto px-2 py-0.5 rounded-full bg-zinc-800 text-xs text-white font-bold">{count}</span>
       </div>
       <div className="flex-1 overflow-y-auto pr-1 min-h-[100px] custom-scrollbar">
          {Array.isArray(tasks) && tasks.filter(t => t.status === status).map(t => <TaskCard key={t.id} task={t} />)}
          {(!Array.isArray(tasks) || tasks.filter(t => t.status === status).length === 0) && (
             <div className="h-32 flex items-center justify-center text-zinc-600 text-xs font-medium italic border-2 border-dashed border-zinc-800/50 rounded-lg">
               Drop item here
             </div>
          )}
       </div>
    </div>
  );

  const pendingCount = Array.isArray(tasks) ? tasks.filter(t => t.status === TaskStatus.PENDING).length : 0;
  const activeCount = Array.isArray(tasks) ? tasks.filter(t => t.status === TaskStatus.IN_PROGRESS).length : 0;
  const completedCount = Array.isArray(tasks) ? tasks.filter(t => t.status === TaskStatus.COMPLETED).length : 0;

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
         <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Mission Control</h1>
            <p className="text-sm text-zinc-500 font-medium">Manage operational directives and assignments</p>
         </div>
         <button 
           onClick={() => setIsModalOpen(true)}
           className="bg-white text-black px-4 py-2.5 rounded-lg hover:bg-zinc-200 transition-all font-bold text-sm flex items-center gap-2 shadow-lg shadow-white/5"
         >
            <Plus size={16} />
            Create Mission
         </button>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 min-h-0">
        <Column 
          status={TaskStatus.PENDING} 
          title="Pending" 
          icon={Clock} 
          count={pendingCount}
        />
        <Column 
          status={TaskStatus.IN_PROGRESS} 
          title="Active" 
          icon={Activity} 
          count={activeCount}
        />
        <Column 
          status={TaskStatus.COMPLETED} 
          title="Completed" 
          icon={CheckCircle} 
          count={completedCount}
        />
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
           <div className="bg-surface border border-zinc-800 rounded-xl w-full max-w-lg shadow-2xl flex flex-col max-h-[90vh]">
              <div className="p-5 border-b border-zinc-800 flex justify-between items-center">
                 <h2 className="text-white font-bold text-lg">New Mission Directive</h2>
                 <button onClick={() => setIsModalOpen(false)} className="text-zinc-500 hover:text-white"><X size={20}/></button>
              </div>
              
              <div className="p-6 space-y-5 overflow-y-auto">
                 <div>
                    <label className="block text-xs font-bold text-zinc-500 mb-1.5 uppercase">Mission Codename</label>
                    <input 
                      className="w-full bg-zinc-900 border border-zinc-700 rounded p-2.5 text-white focus:border-white focus:outline-none focus:ring-1 focus:ring-white transition-all font-medium" 
                      value={newTaskTitle}
                      onChange={e => setNewTaskTitle(e.target.value)}
                      placeholder="e.g. ALPHA_SWEEP_01"
                    />
                 </div>
                 
                 <div>
                    <label className="block text-xs font-bold text-zinc-500 mb-1.5 uppercase">Priority Level</label>
                    <select 
                      className="w-full bg-zinc-900 border border-zinc-700 rounded p-2.5 text-white focus:border-white focus:outline-none"
                      value={newTaskPriority}
                      onChange={e => setNewTaskPriority(e.target.value as TaskPriority)}
                    >
                       {Object.values(TaskPriority).map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                 </div>

                 <div>
                    <label className="block text-xs font-bold text-zinc-500 mb-1.5 uppercase">Mission Briefing</label>
                    <textarea 
                      className="w-full bg-zinc-900 border border-zinc-700 rounded p-2.5 text-white focus:border-white focus:outline-none h-24 resize-none text-sm" 
                      value={newTaskDesc}
                      onChange={e => setNewTaskDesc(e.target.value)}
                      placeholder="Detailed objectives..."
                    />
                 </div>

                 <div>
                    <label className="block text-xs font-bold text-zinc-500 mb-2 uppercase">Assign Assets</label>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-1">
                       {drones.map(drone => (
                          <div 
                            key={drone.id} 
                            onClick={() => toggleDroneSelection(drone.id)}
                            className={cn(
                                "p-2.5 rounded border cursor-pointer flex items-center justify-between text-xs font-bold transition-all",
                                selectedDrones.includes(drone.id) 
                                ? 'bg-white text-black border-white' 
                                : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:border-zinc-600'
                            )}
                          >
                             <span>{drone.name || `Unit ${drone.id}`}</span>
                             {selectedDrones.includes(drone.id) && <CheckCircle size={14} className="fill-black text-white"/>}
                          </div>
                       ))}
                    </div>
                 </div>
              </div>

              <div className="p-5 border-t border-zinc-800 flex justify-end gap-3 bg-zinc-900/50 rounded-b-xl">
                 <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-zinc-400 hover:text-white text-sm font-bold transition-colors">Cancel</button>
                 <button 
                   onClick={handleCreateTask}
                   disabled={!newTaskTitle}
                   className="bg-white text-black font-bold px-6 py-2 rounded hover:bg-zinc-200 transition-colors disabled:opacity-50 text-sm shadow-lg"
                 >
                    Confirm Order
                 </button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
};
