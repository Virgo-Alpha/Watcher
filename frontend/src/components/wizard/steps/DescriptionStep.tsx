import React from 'react';
import './DescriptionStep.css';

interface DescriptionStepProps {
  description: string;
  name: string;
  onChange: (updates: { description?: string; name?: string }) => void;
}

const DescriptionStep: React.FC<DescriptionStepProps> = ({ description, name, onChange }) => {
  return (
    <div className="description-step">
      <h3>Describe what you want to monitor</h3>
      <p className="step-description">
        Use natural language to describe what changes you want to track. Our AI will convert this into
        technical selectors automatically.
      </p>

      <div className="form-group">
        <label htmlFor="name-input">Haunt Name</label>
        <input
          id="name-input"
          type="text"
          className="name-input"
          value={name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="e.g., Job Application Status"
          autoFocus
        />
      </div>

      <div className="form-group">
        <label htmlFor="description-input">Description</label>
        <textarea
          id="description-input"
          className="description-input"
          value={description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Describe what to monitor..."
          rows={6}
        />
        <span className="input-hint">
          Be specific about what elements you want to track and what changes matter to you.
        </span>
      </div>

      <div className="description-examples">
        <h4>Example Descriptions:</h4>
        <div className="example-card">
          <strong>Job Application:</strong>
          <p>
            "Monitor the application status field. Alert me when it changes from 'Under Review' to
            'Interview Scheduled' or any other status."
          </p>
        </div>
        <div className="example-card">
          <strong>Course Enrollment:</strong>
          <p>
            "Track the enrollment status and available seats. Notify me when seats become available
            or when the status changes to 'Open'."
          </p>
        </div>
        <div className="example-card">
          <strong>Product Availability:</strong>
          <p>
            "Watch the stock status and price. Alert me when the item is back in stock or when the
            price drops below $100."
          </p>
        </div>
      </div>
    </div>
  );
};

export default DescriptionStep;
