import React, { useState } from 'react';
import './URLStep.css';

interface URLStepProps {
  url: string;
  onChange: (url: string) => void;
}

const URLStep: React.FC<URLStepProps> = ({ url, onChange }) => {
  const [isValid, setIsValid] = useState(true);

  const validateURL = (value: string): boolean => {
    if (!value) return true; // Empty is valid (will be caught by disabled button)
    
    try {
      const urlObj = new URL(value);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onChange(value);
    setIsValid(validateURL(value));
  };

  return (
    <div className="url-step">
      <h3>Enter the URL you want to monitor</h3>
      <p className="step-description">
        Provide the full URL of the website or page you want to track for changes.
      </p>

      <div className="form-group">
        <label htmlFor="url-input">Website URL</label>
        <input
          id="url-input"
          type="url"
          className={`url-input ${!isValid ? 'invalid' : ''}`}
          value={url}
          onChange={handleChange}
          placeholder="https://example.com/page"
          autoFocus
        />
        {!isValid && (
          <span className="validation-error">
            Please enter a valid HTTP or HTTPS URL
          </span>
        )}
      </div>

      <div className="url-examples">
        <h4>Examples:</h4>
        <ul>
          <li>Job application status page</li>
          <li>Course enrollment page</li>
          <li>Product availability page</li>
          <li>API status dashboard</li>
        </ul>
      </div>
    </div>
  );
};

export default URLStep;
