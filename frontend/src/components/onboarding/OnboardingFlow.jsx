import { useState } from 'react';
import { userApi } from '../../api/userApi';
import { styles } from '../../utils/styles';

const questions = [
  {
    key: 'goals',
    title: 'What are your primary goals?',
    description: 'e.g. Study, Work, Fitness, Personal Projects',
  },
  {
    key: 'focus_times',
    title: 'When are your best focus times?',
    description: 'e.g. Early Morning, Late Night, After Lunch',
  },
  {
    key: 'typical_disruptions',
    title: 'What are your typical disruptions?',
    description: 'e.g. Social media, meetings, noise',
  },
  {
    key: 'structure_preference',
    title: 'How do you prefer your schedule?',
    description: 'e.g. Strict schedule vs Flexible blocks',
  },
  {
    key: 'ai_guidance_level',
    title: 'How much AI guidance do you want?',
    description: 'e.g. "Do it all for me" vs "Just gentle nudges"',
  }
];

export const OnboardingFlow = ({ onComplete }) => {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({
    goals: '',
    focus_times: '',
    typical_disruptions: '',
    structure_preference: '',
    ai_guidance_level: '',
  });
  const [saving, setSaving] = useState(false);

  const currentQuestion = questions[step];

  const handleNext = async () => {
    if (step < questions.length - 1) {
      setStep(step + 1);
    } else {
      setSaving(true);
      try {
        await userApi.updateUserProfile({
          ...answers,
          onboarding_completed: true
        });
        onComplete();
      } catch (err) {
        console.error('Failed to complete onboarding:', err);
        setSaving(false);
      }
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#f9fafb'
    }}>
      <div style={{
        ...styles.card,
        width: '100%',
        maxWidth: 500,
        textAlign: 'center',
        padding: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem', color: '#111827' }}>
          Welcome to DailyPlanner!
        </h2>
        <p style={{ color: '#4b5563', marginBottom: '2rem' }}>
          Let's set up your profile ({step + 1} of {questions.length})
        </p>

        <div style={{ marginBottom: '2rem', textAlign: 'left' }}>
          <label style={styles.label}>{currentQuestion.title}</label>
          <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            {currentQuestion.description}
          </p>
          <input
            style={styles.input}
            value={answers[currentQuestion.key]}
            onChange={(e) => setAnswers({ ...answers, [currentQuestion.key]: e.target.value })}
            placeholder="Type your answer here..."
            autoFocus
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <button
            style={{ ...styles.button, backgroundColor: '#f3f4f6', color: '#374151' }}
            onClick={handleBack}
            disabled={step === 0 || saving}
          >
            Back
          </button>
          <button
            style={styles.button}
            onClick={handleNext}
            disabled={saving}
          >
            {saving ? 'Saving...' : step === questions.length - 1 ? 'Complete Setup' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};
