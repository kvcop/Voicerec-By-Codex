import React from 'react';
import { useTranslations } from '../../i18n';
import { uploadMeetingAudio, MeetingUploadError } from '../../api/uploadMeeting';
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
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files && event.target.files.length > 0 ? event.target.files[0] : null;
    setSelectedFile(file);
    if (feedback) {
      setFeedback(null);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setFeedback({ type: 'error', message: t('uploadForm.error.noFile') });
      return;
    }

    setIsSubmitting(true);
    setFeedback({ type: 'info', message: t('uploadForm.uploading') });

    try {
      const meetingId = await uploadMeetingAudio(selectedFile);
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
    }
  };

  return (
    <section className={[styles.container, className].filter(Boolean).join(' ')}>
      <h2 className={styles.title}>{t('uploadForm.title')}</h2>
      <p className={styles.description}>{t('uploadForm.description')}</p>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.fileLabel} htmlFor="meeting-audio">
          <span>{t('uploadForm.chooseFile')}</span>
          <input
            ref={fileInputRef}
            id="meeting-audio"
            name="meeting-audio"
            type="file"
            accept="audio/wav"
            onChange={handleFileChange}
            disabled={isSubmitting}
          />
        </label>
        {selectedFile ? (
          <span className={styles.fileName}>{selectedFile.name}</span>
        ) : (
          <span className={styles.fileName}>{t('uploadForm.noFileSelected')}</span>
        )}
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
