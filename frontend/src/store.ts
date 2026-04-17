import { create } from 'zustand';

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
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  projects: Project[];
  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentWorkspace: (workspace: Workspace) => void;
  setProjects: (projects: Project[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentWorkspace: null,
  workspaces: [],
  projects: [],
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
  setProjects: (projects) => set({ projects }),
}));
