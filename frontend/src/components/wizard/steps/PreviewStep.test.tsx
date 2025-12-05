import React from 'react';
import { render, screen } from '@testing-library/react';
import PreviewStep from './PreviewStep';
import { TestScrapeResponse } from '../../../types';

describe('PreviewStep', () => {
  const baseProps = {
    url: 'https://example.com',
    name: 'Test Haunt',
    description: 'Test description',
  };

  it('renders without crashing with minimal config', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status-element',
        },
      },
      extracted_data: {},
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    expect(screen.getByText('Preview Configuration')).toBeInTheDocument();
  });

  it('handles config without normalization field', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
      },
      extracted_data: {},
    };

    expect(() => {
      render(<PreviewStep {...baseProps} previewData={previewData} />);
    }).not.toThrow();
  });

  it('handles config without truthy_values field', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
      },
      extracted_data: {},
    };

    expect(() => {
      render(<PreviewStep {...baseProps} previewData={previewData} />);
    }).not.toThrow();
  });

  it('displays extracted data when available', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
      },
      extracted_data: {
        status: 'Open',
        count: '42',
      },
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    expect(screen.getByText('Extracted Data')).toBeInTheDocument();
    expect(screen.getByText('status:')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
  });

  it('shows no data message when extracted_data is empty', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
      },
      extracted_data: {},
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    expect(screen.getByText(/No data was extracted/)).toBeInTheDocument();
  });

  it('displays normalization rules when present', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
        normalization: {
          status: 'trim',
        },
      },
      extracted_data: {},
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    const details = screen.getByText('View technical details');
    expect(details).toBeInTheDocument();
  });

  it('displays truthy values when present', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
        truthy_values: {
          status: ['open', 'available'],
        },
      },
      extracted_data: {},
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    const details = screen.getByText('View technical details');
    expect(details).toBeInTheDocument();
  });

  it('displays haunt details correctly', () => {
    const previewData: TestScrapeResponse = {
      success: true,
      config: {
        selectors: {
          status: '.status',
        },
      },
      extracted_data: {},
    };

    render(<PreviewStep {...baseProps} previewData={previewData} />);
    expect(screen.getByText('Test Haunt')).toBeInTheDocument();
    expect(screen.getByText('https://example.com')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });
});
