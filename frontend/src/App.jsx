import React, { useState, useEffect } from 'react';
import ClipCard from './ClipCard';

const App = () => {
  const [formData, setFormData] = useState({
    video_url: '',
    clip_duration: 40,
    clip_count: 5
  });
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [clips, setClips] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'video_url' ? value : parseInt(value) || 0
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setJobId(null);
    setJobStatus(null);
    setClips([]);

    try {
      const response = await fetch('/generate-clips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to submit job');
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus('processing');
    } catch (error) {
      console.error('Error submitting job:', error);
      alert('Failed to submit job. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const pollJobStatus = async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`/jobs/${jobId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }

      const data = await response.json();
      setJobStatus(data.status);

      if (data.status === 'completed' && data.clips) {
        setClips(data.clips);
      }
    } catch (error) {
      console.error('Error polling job status:', error);
    }
  };

  useEffect(() => {
    if (jobId && jobStatus === 'processing') {
      const interval = setInterval(pollJobStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [jobId, jobStatus]);

  return (
    <div className="container">
      <div className="header">
        <h1>Opus MVP - Video Clipper</h1>
        <p>Generate AI-powered clips from YouTube videos</p>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="video_url">YouTube URL</label>
          <input
            type="url"
            id="video_url"
            name="video_url"
            value={formData.video_url}
            onChange={handleInputChange}
            placeholder="https://www.youtube.com/watch?v=..."
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="clip_duration">Clip Duration (seconds)</label>
            <input
              type="number"
              id="clip_duration"
              name="clip_duration"
              value={formData.clip_duration}
              onChange={handleInputChange}
              min="10"
              max="300"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="clip_count">Number of Clips</label>
            <input
              type="number"
              id="clip_count"
              name="clip_count"
              value={formData.clip_count}
              onChange={handleInputChange}
              min="1"
              max="10"
              required
            />
          </div>
        </div>

        <button 
          type="submit" 
          className="submit-btn"
          disabled={isSubmitting || jobStatus === 'processing'}
        >
          {isSubmitting ? 'Submitting...' : 'Generate Clips'}
        </button>
      </form>

      {jobStatus && (
        <div className={`status ${jobStatus === 'processing' ? 'processing' : ''}`}>
          {jobStatus === 'processing' && (
            <p>🔄 Processing your video... This may take a few minutes.</p>
          )}
          {jobStatus === 'completed' && (
            <p>✅ Clips generated successfully!</p>
          )}
          {jobId && <p><small>Job ID: {jobId}</small></p>}
        </div>
      )}

      {clips.length > 0 && (
        <div className="clips-grid">
          {clips.map((clipUrl, index) => (
            <ClipCard 
              key={index} 
              clipUrl={clipUrl} 
              index={index} 
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default App;