#Run the Application
# Run the Flask application
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app, db



app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route("/__version")
def version():
    return {"commit": os.environ.get("VERCEL_GIT_COMMIT_SHA", "local")}

if __name__ == "__main__":
    app.run(debug=True)
    
    
import faulthandler
faulthandler.dump_traceback_later(20, repeat=True)