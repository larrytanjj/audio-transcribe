import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import axios from 'axios';

// Mock axios
vi.mock('axios');

// Mock the components that are causing issues
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    Table: ({ dataSource }) => (
      <div data-testid="mock-table">
        {dataSource?.map((item) => (
          <div key={item.id} data-testid="table-row">
            <span>{item.original_filename}</span>
            <span>{item.unique_filename}</span>
            <span>{item.transcription}</span>
          </div>
        ))}
      </div>
    ),
    Alert: ({ message }) => <div data-testid="alert">{message}</div>,
    Upload: {
      Dragger: () => <div data-testid="upload-dragger">Upload Area</div>
    },
    Input: {
      Search: () => <div data-testid="search-input">Search Box</div>
    },
    Spin: () => <div data-testid="spinner">Loading...</div>
  };
});

// Skip interval timers
vi.mock('react', async () => {
  const actual = await vi.importActual('react');
  return {
    ...actual,
    useEffect: (callback, deps) => {
      // Only run the callback once and skip setInterval
      if (deps?.length === 0) {
        const origSetInterval = global.setInterval;
        global.setInterval = vi.fn();
        callback();
        global.setInterval = origSetInterval;
      } else {
        actual.useEffect(callback, deps);
      }
    }
  };
});

describe('Audio Transcribe', () => {
  beforeEach(() => {
    // Clear all mocks
    vi.resetAllMocks();
    
    // Mock API responses
    axios.request.mockImplementation((config) => {
      // Health check endpoint
      if (config.url === 'http://localhost:8000/health') {
        return Promise.resolve({ 
          data: { status: 'healthy' } 
        });
      }
      
      // Transcriptions endpoint
      if (config.url === 'http://localhost:8000/transcriptions') {
        return Promise.resolve({
          data: [
            { 
              id: '1', 
              original_filename: 'audio1.mp3', 
              unique_filename: '12345',
              transcription: 'This is a test transcription',
              created_at: '2023-01-01'
            },
            { 
              id: '2', 
              original_filename: 'audio2.mp3', 
              unique_filename: '67890',
              transcription: 'Another test transcription',
              created_at: '2023-01-02'
            }
          ]
        });
      }
      
      return Promise.reject(new Error('Not mocked'));
    });
  });

  it('renders basic UI elements when service is online', async () => {
    // Set a long timeout
    vi.setConfig({ testTimeout: 30000 });
    
    render(<App />);
    
    // Check for basic UI elements
    expect(await screen.findByTestId('alert')).toBeInTheDocument();
    expect(await screen.findByTestId('upload-dragger')).toBeInTheDocument();
    expect(await screen.findByTestId('search-input')).toBeInTheDocument();
    expect(await screen.findByTestId('mock-table')).toBeInTheDocument();
    
    // Verify API calls
    expect(axios.request).toHaveBeenCalledWith(expect.objectContaining({
      method: 'get',
      url: 'http://localhost:8000/health'
    }));
    
    expect(axios.request).toHaveBeenCalledWith(expect.objectContaining({
      method: 'get',
      url: 'http://localhost:8000/transcriptions'
    }));
  });
  
  it('shows offline status when service is unavailable', async () => {
    // Mock health check to return error
    axios.request.mockImplementationOnce((config) => {
      if (config.url === 'http://localhost:8000/health') {
        return Promise.reject(new Error('Service unavailable'));
      }
      return Promise.reject(new Error('Not mocked'));
    });
    
    render(<App />);
    
    // Alert should contain the offline message
    const alert = await screen.findByTestId('alert');
    expect(alert).toBeInTheDocument();
    expect(alert.textContent).toContain('Service Offline');
    
    // UI elements should not be visible when offline
    expect(screen.queryByTestId('upload-dragger')).not.toBeInTheDocument();
    expect(screen.queryByTestId('search-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('mock-table')).not.toBeInTheDocument();
  });
  
  it('correctly displays transcription data from API', async () => {
    // Custom mock data
    const mockTranscriptions = [
      { 
        id: '100', 
        original_filename: 'important_meeting.mp3', 
        unique_filename: '54321',
        transcription: 'This is a very important discussion about the project timeline',
        created_at: '2023-03-15'
      },
      { 
        id: '101', 
        original_filename: 'interview.mp3', 
        unique_filename: '98765',
        transcription: 'Tell me about your experience with React development',
        created_at: '2023-03-16'
      }
    ];
    
    // Override transcriptions endpoint
    axios.request.mockImplementation((config) => {
      if (config.url === 'http://localhost:8000/health') {
        return Promise.resolve({ data: { status: 'healthy' } });
      }
      
      if (config.url === 'http://localhost:8000/transcriptions') {
        return Promise.resolve({ data: mockTranscriptions });
      }
      
      return Promise.reject(new Error('Not mocked'));
    });
    
    render(<App />);
    
    // Wait for the table to appear
    const table = await screen.findByTestId('mock-table');
    expect(table).toBeInTheDocument();
    
    // Verify our custom transcription data is displayed
    const rows = await screen.findAllByTestId('table-row');
    expect(rows).toHaveLength(2);
    
    // Check for specific text content from our mock data
    expect(table.textContent).toContain('important_meeting.mp3');
    expect(table.textContent).toContain('interview.mp3');
    expect(table.textContent).toContain('This is a very important discussion');
    expect(table.textContent).toContain('Tell me about your experience');
  });
});