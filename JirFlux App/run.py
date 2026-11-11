#Run the Application
# Run the Flask application
from app import create_app, db



app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
    
    
import faulthandler
faulthandler.dump_traceback_later(20, repeat=True)