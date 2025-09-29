import React from 'react';
import { useTranslations } from '../../i18n';
import {
  uploadMeetingAudio,
  MeetingUploadError,
  UploadProgress,
} from '../../api/uploadMeeting';
import styles from './styles.module.css';

interface UploadFormProps {
  onMeetingReady: (meetingId: string) => void;
  className?: string;
}

type FeedbackState = {
  type: 'info' | 'success' | 'error';
  message: string;
};

export default function UploadForm({ onMeetingReady, className }: UploadFormProps) {
  const t = useTranslations();
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [feedback, setFeedback] = React.useState<FeedbackState | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const [progress, setProgress] = React.useState<UploadProgress | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const uploadFieldId = React.useId();

  const resetFeedback = React.useCallback(() => {
    if (feedback) {
      setFeedback(null);
    }
  }, [feedback]);

  const resetForm = React.useCallback(() => {
    setSelectedFile(null);
    setProgress(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const validateAndSelectFile = React.useCallback(
    (file: File | null) => {
      if (!file) {
        setSelectedFile(null);
        return;
      }

      const isWavFile =
        file.type === 'audio/wav' || file.name.toLowerCase().endsWith('.wav');

      if (!isWavFile) {
        setSelectedFile(null);
        setProgress(null);
        setFeedback({ type: 'error', message: t('uploadForm.error.invalidType') });
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }

      resetFeedback();
      setSelectedFile(file);
      setProgress(null);
    },
    [resetFeedback, t]
  );

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files && event.target.files.length > 0 ? event.target.files[0] : null;
    validateAndSelectFile(file);
  };

  const handleDragEnter = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = 'copy';
    if (!isDragging) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const related = event.relatedTarget as Node | null;
    if (related && event.currentTarget.contains(related)) {
      return;
    }
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const file = event.dataTransfer.files && event.dataTransfer.files.length > 0 ? event.dataTransfer.files[0] : null;
    validateAndSelectFile(file);
  };

  const handleProgress = React.useCallback(
    (nextProgress: UploadProgress) => {
      setProgress(nextProgress);
    },
    []
  );

  const formatFileSize = React.useCallback((bytes: number) => {
    if (!Number.isFinite(bytes) || bytes <= 0) {
      return t('uploadForm.fileSizeUnknown');
    }

    const megabytes = bytes / (1024 * 1024);
    if (megabytes >= 1) {
      return `${megabytes.toFixed(megabytes >= 10 ? 0 : 1)} MB`;
    }

    const kilobytes = bytes / 1024;
    return `${kilobytes.toFixed(kilobytes >= 10 ? 0 : 1)} KB`;
  }, [t]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setFeedback({ type: 'error', message: t('uploadForm.error.noFile') });
      return;
    }

    setIsSubmitting(true);
    setFeedback({ type: 'info', message: t('uploadForm.uploading') });
    setProgress({ loaded: 0, total: selectedFile.size || undefined, percent: selectedFile.size ? 0 : null });

    try {
      const meetingId = await uploadMeetingAudio(selectedFile, {
        onProgress: handleProgress,
      });
      setFeedback({ type: 'success', message: t('uploadForm.success', { meetingId }) });
      onMeetingReady(meetingId);
      resetForm();
    } catch (error) {
      if (error instanceof MeetingUploadError) {
        const messageKey = `uploadForm.error.${error.reason}` as const;
        setFeedback({ type: 'error', message: t(messageKey) });
      } else {
        setFeedback({ type: 'error', message: t('uploadForm.error.generic') });
      }
    } finally {
      setIsSubmitting(false);
      setProgress(null);
    }
  };

  return (
    <section className={[styles.container, className].filter(Boolean).join(' ')}>
      <h2 className={styles.title}>{t('uploadForm.title')}</h2>
      <p className={styles.description}>{t('uploadForm.description')}</p>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label
          className={styles.dropZone}
          htmlFor={uploadFieldId}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          data-dragging={isDragging || undefined}
        >
          <input
            ref={fileInputRef}
            id={uploadFieldId}
            name="meeting-audio"
            type="file"
            accept="audio/wav"
            onChange={handleFileChange}
            disabled={isSubmitting}
          />
          <span className={styles.dropZoneTitle}>{t('uploadForm.dropzone.title')}</span>
          <span className={styles.dropZoneSubtitle}>{t('uploadForm.dropzone.subtitle')}</span>
        </label>
        {selectedFile ? (
          <div className={styles.fileDetails}>
            <span className={styles.fileName} title={selectedFile.name}>
              {selectedFile.name}
            </span>
            <span className={styles.fileMeta}>
              {t('uploadForm.fileSize', { size: formatFileSize(selectedFile.size) })}
            </span>
          </div>
        ) : (
          <span className={styles.filePlaceholder}>{t('uploadForm.noFileSelected')}</span>
        )}
        {progress ? (
          <div className={styles.progressSection}>
            <div
              className={styles.progressBar}
              data-indeterminate={progress.percent === null || progress.percent === undefined || Number.isNaN(progress.percent)}
            >
              <div
                className={styles.progressValue}
                style={
                  progress.percent === null || progress.percent === undefined
                    ? undefined
                    : { width: `${Math.min(100, Math.max(0, progress.percent))}%` }
                }
              />
            </div>
            <span className={styles.progressLabel}>
              {progress.percent === null || progress.percent === undefined
                ? t('uploadForm.uploading')
                : t('uploadForm.progress', { percent: progress.percent })}
            </span>
          </div>
        ) : null}
        <button type="submit" className={styles.submit} disabled={isSubmitting}>
          {isSubmitting ? t('uploadForm.uploadingShort') : t('uploadForm.submit')}
        </button>
      </form>
      {feedback ? (
        <p className={styles.feedback} data-variant={feedback.type}>
          {feedback.message}
        </p>
      ) : null}
    </section>
  );
}
