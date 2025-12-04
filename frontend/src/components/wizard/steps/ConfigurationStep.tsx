import React from 'react';
import { Folder } from '../../../types';
import './ConfigurationStep.css';

interface ConfigurationStepProps {
  folder: string | null;
  scrapeInterval: number;
  alertMode: 'once' | 'on_change';
  isPublic: boolean;
  folders: Folder[];
  onChange: (updates: {
    folder?: string | null;
    scrapeInterval?: number;
    alertMode?: 'once' | 'on_change';
    isPublic?: boolean;
  }) => void;
}

const ConfigurationStep: React.FC<ConfigurationStepProps> = ({
  folder,
  scrapeInterval,
  alertMode,
  isPublic,
  folders,
  onChange,
}) => {
  const scrapeIntervals = [
    { value: 15, label: 'Every 15 minutes' },
    { value: 30, label: 'Every 30 minutes' },
    { value: 60, label: 'Every hour' },
    { value: 1440, label: 'Daily' },
  ];

  return (
    <div className="configuration-step">
      <h3>Configure monitoring settings</h3>
      <p className="step-description">
        Choose how often to check for changes and where to organize this haunt.
      </p>

      <div className="form-group">
        <label htmlFor="folder-select">Folder (Optional)</label>
        <select
          id="folder-select"
          className="folder-select"
          value={folder || ''}
          onChange={(e) => onChange({ folder: e.target.value || null })}
        >
          <option value="">No folder</option>
          {folders.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>
        <span className="input-hint">Organize your haunts into folders for easier management</span>
      </div>

      <div className="form-group">
        <label htmlFor="interval-select">Check Frequency</label>
        <select
          id="interval-select"
          className="interval-select"
          value={scrapeInterval}
          onChange={(e) => onChange({ scrapeInterval: parseInt(e.target.value) })}
        >
          {scrapeIntervals.map((interval) => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
        <span className="input-hint">How often should we check for changes?</span>
      </div>

      <div className="form-group">
        <label htmlFor="alert-mode-select">Alert Mode</label>
        <select
          id="alert-mode-select"
          className="alert-mode-select"
          value={alertMode}
          onChange={(e) => onChange({ alertMode: e.target.value as 'once' | 'on_change' })}
        >
          <option value="once">Alert once (first change only)</option>
          <option value="on_change">Alert on every change</option>
        </select>
        <span className="input-hint">
          {alertMode === 'once'
            ? 'You will be notified only the first time a change is detected'
            : 'You will be notified every time a change is detected'}
        </span>
      </div>

      <div className="form-group checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => onChange({ isPublic: e.target.checked })}
          />
          <span>Make this haunt public</span>
        </label>
        <span className="input-hint">
          Public haunts can be discovered and subscribed to by other users
        </span>
      </div>
    </div>
  );
};

export default ConfigurationStep;
