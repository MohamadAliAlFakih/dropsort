type ErrorAlertProps = {
    message: string | null;
  };
  
  export function ErrorAlert({ message }: ErrorAlertProps) {
    if (!message) {
      return null;
    }
  
    return (
      <p className="error" role="alert">
        {message}
      </p>
    );
  }