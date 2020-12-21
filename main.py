import json
from flask import Flask, render_template, make_response
from flask_cors import CORS, cross_origin
from flask_restful import Api, Resource, reqparse
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from operator import itemgetter

app = Flask(__name__)
cors = CORS(app)
api = Api(app)

rgb_post_args = reqparse.RequestParser()
rgb_post_args.add_argument("r", type=int, help="RGB red value")
rgb_post_args.add_argument("g", type=int, help="RGB green value")
rgb_post_args.add_argument("b", type=int, help="RGB blue value")

class Catalog(Resource):
    @cross_origin()
    def get(self):
        args = rgb_post_args.parse_args()
        response = {}

        # Convert POST -> sRGB -> Lab
        post_srgb = sRGBColor(args['r'], args['g'], args['b'])
        post_lab = convert_color(post_srgb, LabColor)

        # Open Ulta catalog
        with open('ulta_catalog.json', 'r') as json_file:
            catalog = json.load(json_file)

            # List of comparison results
            results = []

            # Select polish color to test
            for key in catalog.keys():
                for shade in catalog[key]['shades']:
                    r = catalog[key]['shades'][shade]['colors']['r']
                    g = catalog[key]['shades'][shade]['colors']['g']
                    b = catalog[key]['shades'][shade]['colors']['b']
                    test_srgb = sRGBColor(r, g, b)
                    test_lab = convert_color(test_srgb, LabColor)
                    delta = delta_e_cie2000(test_lab, post_lab)
                    results.append([key, shade, delta])

            sorted_results = sorted(results, key = itemgetter(2))

            for i in range(min(100, len(sorted_results))):
                response[i] = {
                    'name': catalog[str(sorted_results[i][0])]['name'],
                    'brand': catalog[str(sorted_results[i][0])]['brand'],
                    'price': catalog[str(sorted_results[i][0])]['price'],
                    'shade': sorted_results[i][1],
                    'product_url': catalog[str(sorted_results[i][0])]['url'],
                    'shade_url': catalog[str(sorted_results[i][0])]['shades'][sorted_results[i][1]]['image']
                }

        return response

    # @cross_origin()
    # def get(self):
    #     response = make_response(render_template("index.html"))
    #     response.headers['content-type'] = 'html'
    #     return response

api.add_resource(Catalog, '/')

if __name__ == "__main__":
    app.run(debug=True)