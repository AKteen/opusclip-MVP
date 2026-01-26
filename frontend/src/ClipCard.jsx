import React from 'react';

const ClipCard = ({ clipUrl, index }) => {
  return (
    <div className="clip-card">
      <video controls>
        <source src={clipUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className="clip-card-content">
        <h3>Clip {index + 1}</h3>
        <a 
          href={clipUrl} 
          download={`clip-${index + 1}.mp4`}
          className="download-btn"
        >
          Download
        </a>
      </div>
    </div>
  );
};

export default ClipCard;