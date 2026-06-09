import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import api from '../services/api';
import axios from 'axios'; // We use raw axios for S3 to avoid our interceptors

export default function PublisherPortal() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Content List State
  const [contentList, setContentList] = useState([]);
  const [isLoadingContent, setIsLoadingContent] = useState(true);

  // Upload Form State
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [courseCode, setCourseCode] = useState('');
  const [academicYear, setAcademicYear] = useState('');
  
  // Upload Progress State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(''); // 'idle', 'uploading', 'success', 'error'

  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchMyContent();
  }, []);

  const fetchMyContent = async () => {
    try {
      // Stub for now until backend is ready
      // const res = await api.get('/content/my-content');
      // setContentList(res.data);
      setContentList([]);
    } catch (error) {
      console.error("Failed to fetch content", error);
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error("Failed to log out", error);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) setFile(selectedFile);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !title || !courseCode || !academicYear) {
      alert("Please fill all required fields and select a file.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus('uploading');

    try {
      // Step 1: Get Presigned URL
      const presignedRes = await api.post('/content/presigned-url', {
        filename: file.name,
        content_type: file.type
      });

      const { upload_url, file_key } = presignedRes.data;

      // Step 2: Direct Upload to S3 using raw axios
      await axios.put(upload_url, file, {
        headers: {
          'Content-Type': file.type,
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      // Step 3: Confirm Upload Webhook
      await api.post('/content/confirm-upload', {
        file_key,
        title,
        description,
        course_code: courseCode,
        academic_year: academicYear,
        content_type: file.type
      });

      setUploadStatus('success');
      
      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
      setCourseCode('');
      setAcademicYear('');
      if (fileInputRef.current) fileInputRef.current.value = '';

      fetchMyContent();

    } catch (error) {
      console.error("Upload flow failed", error);
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadStatus(''), 5000); // Clear status after 5s
    }
  };

  return (
    <div className="bg-theme-bg text-theme-text min-h-screen flex flex-col antialiased transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-theme-border transition-colors duration-300">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-theme-accent-light border border-theme-accent-light">
            <span className="material-symbols-outlined text-theme-accent text-[24px]">publish</span>
          </div>
          <div>
            <h1 className="font-sans text-[22px] font-semibold leading-[1.2] text-theme-accent">Publisher Portal</h1>
            <span className="text-xs font-mono text-theme-text-muted uppercase tracking-wider">Content Management</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <ThemeToggle />
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-theme-text">{user?.email}</span>
            <span className="text-xs text-theme-text-muted flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-theme-accent inline-block shadow-[0_0_8px_rgba(78,222,163,0.6)]"></span>
              {user?.role} Access
            </span>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all bg-theme-border text-theme-text-strong hover:bg-theme-border-strong border border-theme-border"
          >
            <span className="material-symbols-outlined text-[20px]">logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Upload Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-theme-surface border border-theme-border rounded-3xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-theme-accent">cloud_upload</span>
              Upload Material
            </h2>

            <form onSubmit={handleUpload} className="space-y-4">
              {/* File Dropzone */}
              <div 
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
                  file ? 'border-theme-accent bg-theme-accent-light/10' : 'border-theme-border hover:border-theme-accent hover:bg-theme-bg'
                }`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  className="hidden" 
                  ref={fileInputRef} 
                  onChange={handleFileSelect} 
                  accept=".pdf,.mp4,.md"
                />
                <span className={`material-symbols-outlined text-4xl mb-2 ${file ? 'text-theme-accent' : 'text-theme-text-muted'}`}>
                  {file ? 'draft' : 'upload_file'}
                </span>
                <p className="font-medium text-theme-text">
                  {file ? file.name : 'Click or drag file to upload'}
                </p>
                {file && <p className="text-xs text-theme-text-muted mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>}
              </div>

              {/* Metadata Fields */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-mono text-theme-text-strong uppercase mb-1">Title *</label>
                  <input 
                    type="text" 
                    value={title} onChange={(e) => setTitle(e.target.value)}
                    required
                    className="w-full bg-theme-bg border border-theme-border rounded-xl px-4 py-2 text-theme-text focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent" 
                    placeholder="e.g. Extractive Metallurgy 3rd Ed"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-mono text-theme-text-strong uppercase mb-1">Course Code *</label>
                    <input 
                      type="text" 
                      value={courseCode} onChange={(e) => setCourseCode(e.target.value)}
                      required
                      className="w-full bg-theme-bg border border-theme-border rounded-xl px-4 py-2 text-theme-text focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent" 
                      placeholder="e.g. TPMP"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-theme-text-strong uppercase mb-1">Academic Year *</label>
                    <select 
                      value={academicYear} onChange={(e) => setAcademicYear(e.target.value)}
                      required
                      className="w-full bg-theme-bg border border-theme-border rounded-xl px-4 py-2 text-theme-text focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent"
                    >
                      <option value="" disabled>Select</option>
                      <option value="1st Year">1st Year</option>
                      <option value="2nd Year">2nd Year</option>
                      <option value="3rd Year">3rd Year</option>
                      <option value="4th Year">4th Year</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-theme-text-strong uppercase mb-1">Description</label>
                  <textarea 
                    value={description} onChange={(e) => setDescription(e.target.value)}
                    className="w-full bg-theme-bg border border-theme-border rounded-xl px-4 py-2 text-theme-text focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent h-24 resize-none" 
                    placeholder="Optional details about this material..."
                  ></textarea>
                </div>
              </div>

              {/* Submit / Progress */}
              {isUploading ? (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium text-theme-text">
                    <span>Uploading direct to S3...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-theme-border rounded-full h-2">
                    <div className="bg-theme-accent h-2 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                </div>
              ) : (
                <button 
                  type="submit" 
                  disabled={!file}
                  className="w-full bg-theme-accent text-white font-medium py-3 rounded-xl hover:bg-theme-accent-hover transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-[20px]">backup</span>
                  Start Upload
                </button>
              )}

              {/* Status Message */}
              {uploadStatus === 'success' && <p className="text-sm text-theme-accent text-center mt-2">Upload completed and bound successfully!</p>}
              {uploadStatus === 'error' && <p className="text-sm text-red-500 text-center mt-2">Upload failed. Check console.</p>}
            </form>
          </div>
        </div>

        {/* Right Column: Content List */}
        <div className="lg:col-span-2">
          <div className="bg-theme-surface border border-theme-border rounded-3xl p-6 shadow-sm min-h-[500px] flex flex-col">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-theme-accent">library_books</span>
              My Published Content
            </h2>

            {isLoadingContent ? (
              <div className="flex-1 flex items-center justify-center">
                <span className="material-symbols-outlined animate-spin text-theme-accent text-4xl">refresh</span>
              </div>
            ) : contentList.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-theme-text-muted border-2 border-dashed border-theme-border rounded-2xl p-8">
                <span className="material-symbols-outlined text-5xl mb-3 opacity-50">folder_open</span>
                <p>No content uploaded yet.</p>
                <p className="text-sm mt-1">Use the panel on the left to add your first course material.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-theme-border text-sm font-mono text-theme-text-muted uppercase">
                      <th className="pb-3 font-medium pl-4">Title</th>
                      <th className="pb-3 font-medium">Course</th>
                      <th className="pb-3 font-medium">Type</th>
                      <th className="pb-3 font-medium pr-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contentList.map((item, idx) => (
                      <tr key={idx} className="border-b border-theme-border/50 hover:bg-theme-bg transition-colors group">
                        <td className="py-4 pl-4 font-medium text-theme-text">{item.title}</td>
                        <td className="py-4 text-theme-text-muted">{item.course_code}</td>
                        <td className="py-4 text-theme-text-muted text-sm">{item.content_type.split('/')[1]?.toUpperCase() || 'FILE'}</td>
                        <td className="py-4 pr-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                            PENDING
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
