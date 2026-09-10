import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchTemplates, fetchTemplateById } from '../api/templateApi';
import { PlannerTemplate } from '../types';

interface TemplateContextType {
  templates: PlannerTemplate[];
  activeTemplate: PlannerTemplate | null;
  refreshTemplates: () => Promise<void>;
  loadTemplateTasks: (templateId: string) => Promise<void>;
  loading: boolean;
}

const TemplateContext = createContext<TemplateContextType | undefined>(undefined);

interface TemplateProviderProps {
  children: React.ReactNode;
  profile: any;
}

export const TemplateProvider: React.FC<TemplateProviderProps> = ({ children, profile }) => {
  const [templates, setTemplates] = useState<PlannerTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  const activePlannerId = profile?.active_planner_id;

  const refreshTemplates = async () => {
    try {
      if (templates.length === 0) {
        setLoading(true);
      }
      const data = await fetchTemplates(activePlannerId);
      setTemplates(data);
    } catch (err) {
      console.error("Failed to load templates", err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplateTasks = async (templateId: string) => {
    try {
      const fullTemplate = await fetchTemplateById(templateId);
      setTemplates(prev => prev.map(t => t.id === templateId ? { ...t, template_tasks: fullTemplate.template_tasks } : t));
    } catch (err) {
      console.error("Failed to load template tasks", err);
    }
  };

  useEffect(() => {
    refreshTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePlannerId]);

  const activeTemplate = templates.find(t => t.id === activePlannerId) || null;

  return (
    <TemplateContext.Provider value={{ templates, activeTemplate, refreshTemplates, loadTemplateTasks, loading }}>
      {children}
    </TemplateContext.Provider>
  );
};

export const useTemplates = () => {
  const context = useContext(TemplateContext);
  if (context === undefined) {
    throw new Error('useTemplates must be used within a TemplateProvider');
  }
  return context;
};
