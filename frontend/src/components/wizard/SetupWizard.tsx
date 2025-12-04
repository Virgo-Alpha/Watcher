import React, { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { setShowSetupWizard } from '../../store/slices/uiSlice';
import { createHaunt } from '../../store/slices/hauntsSlice';
import { CreateHauntRequest, TestScrapeResponse } from '../../types';
import apiClient from '../../services/api';
import URLStep from './steps/URLStep';
import DescriptionStep from './steps/DescriptionStep';
import ConfigurationStep from './steps/ConfigurationStep';
import PreviewStep from './steps/PreviewStep';
import './SetupWizard.css';

export type WizardStep = 'url' | 'description' | 'configuration' | 'preview';

interface WizardData {
  url: string;
  description: string;
  name: string;
  folder: string | null;
  scrapeInterval: number;
  alertMode: 'once' | 'on_change';
  isPublic: boolean;
  previewData: TestScrapeResponse | null;
}

const SetupWizard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { showSetupWizard } = useAppSelector((state) => state.ui);
  const { folders } = useAppSelector((state) => state.haunts);

  const [currentStep, setCurrentStep] = useState<WizardStep>('url');
  const [wizardData, setWizardData] = useState<WizardData>({
    url: '',
    description: '',
    name: '',
    folder: null,
    scrapeInterval: 60,
    alertMode: 'on_change',
    isPublic: false,
    previewData: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    dispatch(setShowSetupWizard(false));
    // Reset wizard state
    setCurrentStep('url');
    setWizardData({
      url: '',
      description: '',
      name: '',
      folder: null,
      scrapeInterval: 60,
      alertMode: 'on_change',
      isPublic: false,
      previewData: null,
    });
    setError(null);
  };

  const handleNext = async () => {
    setError(null);

    if (currentStep === 'url') {
      setCurrentStep('description');
    } else if (currentStep === 'description') {
      setCurrentStep('configuration');
    } else if (currentStep === 'configuration') {
      // Run test scrape before showing preview
      setLoading(true);
      try {
        const previewData = await apiClient.testScrape({
          url: wizardData.url,
          description: wizardData.description,
        });
        setWizardData({ ...wizardData, previewData });
        setCurrentStep('preview');
      } catch (err: any) {
        setError(err.message || 'Failed to test scrape. Please check your URL and description.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleBack = () => {
    setError(null);
    if (currentStep === 'description') {
      setCurrentStep('url');
    } else if (currentStep === 'configuration') {
      setCurrentStep('description');
    } else if (currentStep === 'preview') {
      setCurrentStep('configuration');
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    setError(null);

    try {
      const hauntData: CreateHauntRequest = {
        name: wizardData.name,
        url: wizardData.url,
        description: wizardData.description,
        folder: wizardData.folder,
        scrape_interval: wizardData.scrapeInterval,
        alert_mode: wizardData.alertMode,
        is_public: wizardData.isPublic,
      };

      await dispatch(createHaunt(hauntData)).unwrap();
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create haunt. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateWizardData = (updates: Partial<WizardData>) => {
    setWizardData({ ...wizardData, ...updates });
  };

  if (!showSetupWizard) {
    return null;
  }

  const stepTitles: Record<WizardStep, string> = {
    url: 'Enter URL',
    description: 'Describe What to Monitor',
    configuration: 'Configure Settings',
    preview: 'Preview & Confirm',
  };

  const steps: WizardStep[] = ['url', 'description', 'configuration', 'preview'];
  const currentStepIndex = steps.indexOf(currentStep);

  return (
    <div className="wizard-overlay" onClick={handleClose}>
      <div className="wizard-modal" onClick={(e) => e.stopPropagation()}>
        <div className="wizard-header">
          <h2>Create New Haunt</h2>
          <button className="close-button" onClick={handleClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="wizard-progress">
          {steps.map((step, index) => (
            <div
              key={step}
              className={`progress-step ${index <= currentStepIndex ? 'active' : ''} ${
                index === currentStepIndex ? 'current' : ''
              }`}
            >
              <div className="progress-circle">{index + 1}</div>
              <div className="progress-label">{stepTitles[step]}</div>
            </div>
          ))}
        </div>

        <div className="wizard-content">
          {error && (
            <div className="wizard-error">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          {currentStep === 'url' && (
            <URLStep
              url={wizardData.url}
              onChange={(url) => updateWizardData({ url })}
            />
          )}

          {currentStep === 'description' && (
            <DescriptionStep
              description={wizardData.description}
              name={wizardData.name}
              onChange={(updates) => updateWizardData(updates)}
            />
          )}

          {currentStep === 'configuration' && (
            <ConfigurationStep
              folder={wizardData.folder}
              scrapeInterval={wizardData.scrapeInterval}
              alertMode={wizardData.alertMode}
              isPublic={wizardData.isPublic}
              folders={folders}
              onChange={(updates) => updateWizardData(updates)}
            />
          )}

          {currentStep === 'preview' && wizardData.previewData && (
            <PreviewStep
              url={wizardData.url}
              name={wizardData.name}
              description={wizardData.description}
              previewData={wizardData.previewData}
            />
          )}
        </div>

        <div className="wizard-footer">
          <button
            className="wizard-button secondary"
            onClick={handleBack}
            disabled={currentStep === 'url' || loading}
          >
            Back
          </button>

          {currentStep !== 'preview' ? (
            <button
              className="wizard-button primary"
              onClick={handleNext}
              disabled={
                loading ||
                (currentStep === 'url' && !wizardData.url) ||
                (currentStep === 'description' && (!wizardData.description || !wizardData.name))
              }
            >
              {loading ? 'Loading...' : 'Next'}
            </button>
          ) : (
            <button
              className="wizard-button primary"
              onClick={handleComplete}
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Haunt'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
