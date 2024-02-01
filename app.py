from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Resource, Api
from trading_bots import fetch_candlestick_data

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

class Home(Resource):
    def get(self):
        return 'home'

api.add_resource(Home, '/', '/<path:path>')

correct_password = 'please enter app'

class CheckPassword(Resource):
    def post(self):
        password = request.json.get('password')
        if password == correct_password:
            return jsonify({'my-message': 'success'})
        else:
            return jsonify({'message': 'Wrong password'}), 400

api.add_resource(CheckPassword, '/')

class Assets(Resource):
    def get(self):
        return 'assets_info'

class Asset(Resource):
    def get(self, asset = 'BTC', timeframe = '1h'):
        symbol = f'{asset}USDT'
        signals = fetch_candlestick_data(symbol, timeframe.lower())
        return jsonify(signals)


api.add_resource(Assets, '/assets')
api.add_resource(Asset, '/assets/<string:asset>/<string:timeframe>')


if __name__ == '__main__':
    app.run(debug=True)
