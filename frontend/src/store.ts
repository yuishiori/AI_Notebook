import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  name?: string;
  picture_url?: string;
}

interface Workspace {
  id: string;
  name: string;
}

interface Project {
  id: string;
  name: string;
  status: string;
}

interface AppState {
  user: User | null;
  token: string | null;
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  projects: Project[];
  setAuth: (user: User | null, token: string | null) => void;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  setProjects: (projects: Project[]) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token'),
  currentWorkspace: null,
  workspaces: [],
  projects: [],
  setAuth: (user, token) => {
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
    
    if (user) localStorage.setItem('user', JSON.stringify(user));
    else localStorage.removeItem('user');
    
    set({ user, token });
  },
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
  setProjects: (projects) => set({ projects }),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null, currentWorkspace: null, workspaces: [], projects: [] });
  }
}));
