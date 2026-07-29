import { useEffect, useId, useRef, useState } from 'react';

export function PageHeader({ eyebrow, title, description, actions, technical = false }) {
  return (
    <div className={`page-header ${technical ? 'technical' : ''}`}>
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

export function MetricCard({ label, value, detail, tone = 'brand' }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      {detail && <span>{detail}</span>}
    </article>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-mark" aria-hidden="true">+</span>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function LoadingBlock({ label = 'Loading' }) {
  return (
    <div className="loading-block" role="status">
      <span className="loading-line" />
      <span className="loading-line short" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function StatusNotice({ type = 'info', children }) {
  return <div className={`status-notice ${type}`} role={type === 'error' ? 'alert' : 'status'}>{children}</div>;
}

export function FileUploadField({ id, file, onChange }) {
  return (
    <label className="file-upload-field" htmlFor={id}>
      <span>Upload a PDF</span>
      <span className="file-upload-dropzone">
        <span className="file-upload-mark" aria-hidden="true">↑</span>
        <span className="file-upload-copy">
          <strong>{file?.name || 'Choose a PDF file'}</strong>
          <small>{file ? 'Ready to add to this learning space' : 'PDF files up to 20 MB'}</small>
        </span>
        <span className="file-upload-action">{file ? 'Change' : 'Browse'}</span>
      </span>
      <input
        className="file-upload-input"
        id={id}
        type="file"
        aria-label="Upload a PDF"
        accept="application/pdf,.pdf"
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
    </label>
  );
}

export function Modal({ title, children, onClose, wide = false }) {
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section
        className={`modal ${wide ? 'modal-wide' : ''}`}
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="text-button" onClick={onClose}>Close</button>
        </div>
        {children}
      </section>
    </div>
  );
}

export function ConfirmDialog({ title, description, confirmLabel, onClose, onConfirm, busy = false }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="confirm-dialog-copy">{description}</p>
      <div className="form-actions">
        <button className="button secondary" type="button" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="button danger" type="button" onClick={onConfirm} disabled={busy}>
          {busy ? 'Working...' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}

export function ScoreBar({ value, tone = 'brand', label }) {
  const safeValue = Math.max(0, Math.min(100, value || 0));
  return (
    <div className="score-bar-wrap" aria-label={label || `${safeValue}%`}>
      <div className="score-bar-track">
        <span className={`score-bar-fill tone-${tone}`} style={{ width: `${safeValue}%` }} />
      </div>
      {label && <span>{label}</span>}
    </div>
  );
}

export function SelectField({
  label,
  value,
  onChange,
  options,
  disabled = false,
  placeholder = 'Select an option',
}) {
  const [open, setOpen] = useState(false);
  const fieldRef = useRef(null);
  const listboxId = useId();
  const selectedIndex = options.findIndex((option) => option.value === value);
  const selectedOption = options[selectedIndex];

  useEffect(() => {
    function handleOutsideClick(event) {
      if (!fieldRef.current?.contains(event.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  function choose(option) {
    onChange(option.value);
    setOpen(false);
  }

  function handleKeyDown(event) {
    if (disabled) return;
    if (event.key === 'Escape') {
      setOpen(false);
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setOpen((current) => !current);
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const direction = event.key === 'ArrowDown' ? 1 : -1;
      const start = selectedIndex >= 0 ? selectedIndex : direction > 0 ? -1 : 0;
      const nextIndex = (start + direction + options.length) % options.length;
      if (options[nextIndex]) onChange(options[nextIndex].value);
      setOpen(true);
    }
  }

  return (
    <div className="select-field" ref={fieldRef}>
      <span className="select-label">{label}</span>
      <button
        className={`select-trigger ${open ? 'open' : ''}`}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-haspopup="listbox"
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleKeyDown}
      >
        <span className={selectedOption ? '' : 'select-placeholder'}>
          {selectedOption?.label || placeholder}
        </span>
        <span className="select-chevron" aria-hidden="true" />
      </button>
      {open && (
        <div className="select-menu" id={listboxId} role="listbox" aria-label={label}>
          {options.map((option) => {
            const selected = option.value === value;
            return (
              <button
                className={`select-option ${selected ? 'selected' : ''}`}
                type="button"
                role="option"
                aria-selected={selected}
                key={option.value}
                onClick={() => choose(option)}
              >
                <span>{option.label}</span>
                {selected && <span className="select-check" aria-hidden="true">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
