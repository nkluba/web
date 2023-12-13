from flask import Flask, render_template, request, jsonify
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(
    dbname="peatus",
    user="lubandust",
    password="J9fF3NPzVeXW",
    host="ep-holy-cake-07968363.eu-central-1.aws.neon.tech",
    sslmode="require"
)