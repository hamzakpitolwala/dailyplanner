import { styles } from '../../utils/styles';
import { REASON_CODES, ALTERNATE_PRESETS } from '../../utils/constants';

export const CheckinModal = ({
  checkinModal,
  setCheckinModal,
  checkinNotes,
  setCheckinNotes,
  reasonCode,
  setReasonCode,
  reasonText,
  setReasonText,
  altDescription,
  setAltDescription,
  altCategory,
  setAltCategory,
  targetDate,
  setTargetDate,
  handleCheckinModalSubmit
}) => {
  if (!checkinModal) return null;

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modal}>
        <h2 style={{ marginTop: 0 }}>Check-in details</h2>
        <form onSubmit={handleCheckinModalSubmit} style={styles.form}>
          <p style={styles.muted}>
            Marking <strong>{checkinModal.activity.title}</strong> as{' '}
            {checkinModal.status.replace('_', ' ')}
          </p>

          <label style={styles.label}>
            General Notes (optional)
            <textarea
              style={styles.textarea}
              value={checkinNotes}
              onChange={(e) => setCheckinNotes(e.target.value)}
              placeholder="Any context to add?"
            />
          </label>

          {checkinModal.status === 'rescheduled' && (
            <label style={styles.label}>
              Reschedule to date
              <input
                style={styles.input}
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                required
              />
            </label>
          )}

          {checkinModal.status === 'not_done' && checkinModal.activity.policy?.requires_reason !== false && (
            <>
              <label style={styles.label}>
                Why wasn't this completed?
                <select
                  style={styles.input}
                  value={reasonCode}
                  onChange={(e) => setReasonCode(e.target.value)}
                  required
                >
                  <option value="">Select a reason…</option>
                  {REASON_CODES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </label>
              {reasonCode && (
                <label style={styles.label}>
                  Additional detail (optional)
                  <input
                    style={styles.input}
                    value={reasonText}
                    onChange={(e) => setReasonText(e.target.value)}
                    placeholder="Explain further…"
                  />
                </label>
              )}
            </>
          )}

          {checkinModal.status === 'not_done' && checkinModal.activity.policy?.allows_alternate !== false && (
            <>
              <label style={styles.label}>
                What did you do instead? (optional)
                <select
                  style={styles.input}
                  value={altDescription}
                  onChange={(e) => setAltDescription(e.target.value)}
                >
                  <option value="">Select or type below…</option>
                  {ALTERNATE_PRESETS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
                <input
                  style={{ ...styles.input, marginTop: '0.35rem' }}
                  value={altDescription}
                  onChange={(e) => setAltDescription(e.target.value)}
                  placeholder="Or type a custom description…"
                />
              </label>
              {altDescription && (
                <label style={styles.label}>
                  Category (optional)
                  <input
                    style={styles.input}
                    value={altCategory}
                    onChange={(e) => setAltCategory(e.target.value)}
                    placeholder="e.g. work, personal, errands"
                  />
                </label>
              )}
            </>
          )}

          <div style={styles.actions}>
            <button style={styles.primaryButton} type="submit">
              Submit check-in
            </button>
            <button
              style={styles.button}
              type="button"
              onClick={() => setCheckinModal(null)}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
