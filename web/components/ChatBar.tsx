import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, SendHorizontal, X, File, Image as ImageIcon, FileText, Play, Eye, Trash2 } from 'lucide-react';
import { AttachedFile } from '../types';

interface ChatBarProps {
  disabled: boolean;
  onSendMessage: (text: string, files: AttachedFile[]) => void;
}

export const ChatBar: React.FC<ChatBarProps> = ({ disabled, onSendMessage }) => {
  const [input, setInput] = useState('');
  const [showAttach, setShowAttach] = useState(false);
  const [files, setFiles] = useState<AttachedFile[]>([]);
  const [previewFile, setPreviewFile] = useState<AttachedFile | null>(null); // For Lightbox
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Click outside to close attach menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowAttach(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      Array.from(e.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (ev) => {
          if (ev.target?.result) {
            const base64 = (ev.target.result as string).split(',')[1];
            setFiles(prev => [...prev, {
              id: Math.random().toString(36).substr(2, 9),
              name: file.name,
              size: file.size,
              type: file.type,
              data: base64
            }]);
          }
        };
        reader.readAsDataURL(file);
      });
    }
    setShowAttach(false);
    // Reset input so same file can be selected again if needed
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
    if (previewFile?.id === id) setPreviewFile(null);
  };

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!input.trim() && files.length === 0) || disabled) return;
    onSendMessage(input, files);
    setInput('');
    setFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getFileSrc = (file: AttachedFile) => `data:${file.type};base64,${file.data}`;

  return (
    <>
      {/* Main Chat Bar Container */}
      <div 
          ref={wrapperRef}
          className={`absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-30 transition-all duration-500 ease-[cubic-bezier(0.25,0.8,0.25,1)] ${disabled ? 'opacity-0 translate-y-12 pointer-events-none scale-90' : 'opacity-100 translate-y-0 scale-100'}`}
      >
        
        {/* Rich File Previews (Frames on top) */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-3 mb-4 justify-center animate-slide-up px-4">
            {files.map(file => {
              const isImage = file.type.startsWith('image/');
              const isVideo = file.type.startsWith('video/');
              
              return (
                <div key={file.id} className="relative group w-24 h-24 rounded-xl overflow-hidden bg-white shadow-md border border-slate-200 transition-transform hover:scale-105">
                  {/* Media Content */}
                  {isImage ? (
                    <img src={getFileSrc(file)} alt={file.name} className="w-full h-full object-cover" />
                  ) : isVideo ? (
                    <video src={getFileSrc(file)} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-50 text-slate-400 p-2">
                      <FileText size={24} />
                      <span className="text-[9px] mt-1 text-center leading-tight line-clamp-2">{file.type}</span>
                    </div>
                  )}

                  {/* Video Indicator if no hover */}
                  {isVideo && (
                     <div className="absolute inset-0 flex items-center justify-center pointer-events-none group-hover:opacity-0">
                        <div className="bg-black/30 rounded-full p-1.5 backdrop-blur-sm">
                           <Play size={12} fill="white" className="text-white ml-0.5" />
                        </div>
                     </div>
                  )}

                  {/* Hover Overlay with Functions */}
                  <div className="absolute inset-0 bg-slate-900/80 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-2 p-1 backdrop-blur-[2px]">
                    <div className="flex gap-2">
                       <button 
                          onClick={() => setPreviewFile(file)}
                          className="p-1.5 bg-white/10 hover:bg-blue-500 rounded-full text-white transition-colors"
                          title="View"
                       >
                          {isVideo ? <Play size={14} fill="currentColor" /> : <Eye size={14} />}
                       </button>
                       <button 
                          onClick={() => removeFile(file.id)}
                          className="p-1.5 bg-white/10 hover:bg-red-500 rounded-full text-white transition-colors"
                          title="Delete"
                       >
                          <Trash2 size={14} />
                       </button>
                    </div>
                    <span className="text-[9px] text-white/90 font-medium px-1 text-center truncate w-full">
                      {file.name}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Input Bar */}
        <div className="relative bg-white/70 backdrop-blur-2xl border border-white/50 shadow-2xl shadow-blue-900/5 rounded-[2rem] p-2 flex items-end transition-shadow duration-300 hover:shadow-blue-900/10 hover:bg-white/80">
          
          {/* Attachment Button */}
          <div className="relative">
            <button 
              onClick={() => setShowAttach(!showAttach)}
              className={`w-11 h-11 flex items-center justify-center rounded-full transition-all duration-300 ${showAttach ? 'bg-slate-200 text-slate-800 rotate-45' : 'hover:bg-slate-100 text-slate-500'}`}
            >
              <Paperclip size={20} />
            </button>

            {/* Elegant Attachment Popover */}
            {showAttach && (
              <div className="absolute bottom-full left-0 mb-4 bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl border border-white/60 p-1.5 w-60 flex flex-col gap-1 overflow-hidden animate-slide-up origin-bottom-left z-50">
                <div className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Attach Media</div>
                
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="group flex items-center gap-3 px-3 py-3 text-sm text-slate-600 hover:bg-slate-50 rounded-xl transition-all text-left"
                >
                  <div className="bg-blue-100/50 group-hover:bg-blue-100 p-2.5 rounded-xl transition-colors text-blue-600">
                    <ImageIcon size={18} />
                  </div>
                  <div>
                      <span className="block font-semibold text-slate-700">Photos & Videos</span>
                      <span className="block text-[10px] text-slate-400 font-medium">Upload from device</span>
                  </div>
                </button>
                
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="group flex items-center gap-3 px-3 py-3 text-sm text-slate-600 hover:bg-slate-50 rounded-xl transition-all text-left"
                >
                  <div className="bg-purple-100/50 group-hover:bg-purple-100 p-2.5 rounded-xl transition-colors text-purple-600">
                     <FileText size={18} />
                  </div>
                  <div>
                      <span className="block font-semibold text-slate-700">Documents</span>
                      <span className="block text-[10px] text-slate-400 font-medium">PDF, DOCX, TXT</span>
                  </div>
                </button>
              </div>
            )}
            <input 
              type="file" 
              multiple 
              ref={fileInputRef} 
              className="hidden" 
              onChange={handleFileSelect} 
            />
          </div>

          {/* Text Input */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Send a message..."
            className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none resize-none max-h-32 min-h-[44px] py-3 px-3 text-slate-700 placeholder:text-slate-400/80 text-[15px] leading-relaxed scrollbar-hide font-medium"
            rows={1}
            style={{ boxShadow: 'none' }} 
          />

          {/* Send Button */}
          <button 
            onClick={() => handleSubmit()}
            disabled={(!input.trim() && files.length === 0) || disabled}
            className="w-11 h-11 flex items-center justify-center rounded-full bg-slate-900 hover:bg-black text-white shadow-lg shadow-slate-500/20 transition-all disabled:opacity-0 disabled:scale-75 disabled:shadow-none mb-0 ml-1 active:scale-90"
          >
            <SendHorizontal size={20} />
          </button>
        </div>
      </div>

      {/* Lightbox for Viewing/Playing Media */}
      {previewFile && (
        <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-md flex items-center justify-center animate-fade-in p-8" onClick={() => setPreviewFile(null)}>
           <button 
              className="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              onClick={() => setPreviewFile(null)}
           >
              <X size={24} />
           </button>
           
           <div className="max-w-5xl max-h-full flex flex-col items-center" onClick={e => e.stopPropagation()}>
              {previewFile.type.startsWith('image/') ? (
                 <img 
                    src={getFileSrc(previewFile)} 
                    alt={previewFile.name} 
                    className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl" 
                 />
              ) : previewFile.type.startsWith('video/') ? (
                 <video 
                    src={getFileSrc(previewFile)} 
                    controls 
                    autoPlay 
                    className="max-w-full max-h-[85vh] rounded-lg shadow-2xl" 
                 />
              ) : (
                 <div className="bg-white p-12 rounded-2xl flex flex-col items-center gap-4">
                    <FileText size={64} className="text-slate-400" />
                    <p className="text-xl font-medium text-slate-700">{previewFile.name}</p>
                    <p className="text-slate-500">Preview not available for this file type</p>
                 </div>
              )}
              <div className="mt-4 text-white/70 font-medium text-sm tracking-wide">
                 {previewFile.name}
              </div>
           </div>
        </div>
      )}
    </>
  );
};