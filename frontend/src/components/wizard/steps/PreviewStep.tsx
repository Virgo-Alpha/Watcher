import React from 'react';
import { TestScrapeResponse } from '../../../types';
import './PreviewStep.css';

interface PreviewStepProps {
  url: string;
  name: string;
  description: string;
  previewData: TestScrapeResponse;
}

const PreviewStep: React.FC<PreviewStepProps> = ({ url, name, description, previewData }) => {
  const { config, extracted_data } = previewData;

  return (
    <div className="preview-step">
      <h3>Preview extracted data</h3>
      <p className="step-description">
        Here's what we found on the page. If this looks correct, click "Create Haunt" to start monitoring.
      </p>

      <div className="preview-section">
        <h4>Haunt Details</h4>
        <div className="detail-row">
          <span className="detail-label">Name:</span>
          <span className="detail-value">{name}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">URL:</span>
          <span className="detail-value url-value">{url}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Description:</span>
          <span className="detail-value">{description}</span>
        </div>
      </div>

      <div className="preview-section">
        <h4>Extracted Data</h4>
        {Object.keys(extracted_data).length > 0 ? (
          <div className="extracted-data">
            {Object.entries(extracted_data).map(([key, value]) => (
              <div key={key} className="data-row">
                <span className="data-key">{key}:</span>
                <span className="data-value">{String(value)}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-data">
            <p>No data was extracted. This might mean:</p>
            <ul>
              <li>The page requires JavaScript to load content</li>
              <li>The description needs to be more specific</li>
              <li>The page structure is different than expected</li>
            </ul>
            <p>You can still create the haunt and adjust the configuration later.</p>
          </div>
        )}
      </div>

      <div className="preview-section">
        <h4>Generated Configuration</h4>
        <details className="config-details">
          <summary>View technical details</summary>
          <div className="config-content">
            <div className="config-subsection">
              <h5>Selectors</h5>
              <pre>{JSON.stringify(config.selectors, null, 2)}</pre>
            </div>
            {Object.keys(config.normalization).length > 0 && (
              <div className="config-subsection">
                <h5>Normalization Rules</h5>
                <pre>{JSON.stringify(config.normalization, null, 2)}</pre>
              </div>
            )}
            {Object.keys(config.truthy_values).length > 0 && (
              <div className="config-subsection">
                <h5>Truthy Values</h5>
                <pre>{JSON.stringify(config.truthy_values, null, 2)}</pre>
              </div>
            )}
          </div>
        </details>
      </div>

      <div className="preview-note">
        <span className="note-icon">ℹ️</span>
        <span>
          Once created, the haunt will start monitoring according to your schedule. You can edit the
          configuration at any time from the haunt settings.
        </span>
      </div>
    </div>
  );
};

export default PreviewStep;
