import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import styles from './styles.module.css';

type DialogProps = React.ComponentProps<typeof DialogPrimitive.Root> & {
  triggerText: string;
  children: React.ReactNode;
};

export function Dialog({ triggerText, children, ...props }: DialogProps) {
  return (
    <DialogPrimitive.Root {...props}>
      <DialogPrimitive.Trigger className={styles.trigger}>
        {triggerText}
      </DialogPrimitive.Trigger>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className={styles.overlay} />
        <DialogPrimitive.Content className={styles.content}>
          {children}
          <DialogPrimitive.Close className={styles.close}>
            Close
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export default Dialog;
