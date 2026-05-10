
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# 20 students. Each row is one student.Features: how many hours they studied, attendance %, sleep hours,Label: did they pass (1) or fail (0)
data = {
    'study_hours': [1, 2, 1, 5, 6, 7, 3, 2, 8, 7, 4, 1, 6, 5, 3, 8, 2, 7, 4, 1],
    'attendance':  [40,50,30,80,90,95,60,45,98,85,70,35,88,75,55,92,48,89,65,25],
    'sleep_hours': [4, 5, 3, 7, 8, 7, 6, 4, 8, 7, 6, 4, 7, 6, 5, 8, 5, 7, 6, 3],
    'result':      [0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0]
    # 0 = fail, 1 = pass
}

df = pd.DataFrame(data)
print(df.to_string(index=False))
print()

# X = what we know about each student (features)
# y = what we want to predict (pass or fail)
X = df[['study_hours', 'attendance', 'sleep_hours']]
y = df['result']

print(X.to_string(index=False))
print(y.to_string(index=False))

# 80% for training, 20% for testing

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training rows : {len(X_train)}")
print(f"Testing rows  : {len(X_test)}")
print()


# max_depth=3 means the tree can ask at most 3 questions
# This stops it from memorising the data

tree = DecisionTreeClassifier(max_depth=3, random_state=42)
tree.fit(X_train, y_train)
# Which of the 3 features did the tree find most useful?
importances = tree.feature_importances_
#feature_importances_ is just the result of that tracking. It is a list of scores, one score per feature, that adds up to exactly 1.0.
feature_names = ['study_hours', 'attendance', 'sleep_hours']

print("which feature matters most,...?")
print(importances)


predictions = tree.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"  Predicted : {list(predictions)}")
print(f"  Actual    : {list(y_test)}")
print(f"  Accuracy  : {accuracy * 100:.0f}%")


new_student = pd.DataFrame([[6, 85, 7]], columns=['study_hours', 'attendance', 'sleep_hours'])
prediction = tree.predict(new_student)
probability = tree.predict_proba(new_student)

print("PREDICT A NEW STUDENT")
print(f"  study_hours : 6")
print(f"  attendance  : 85%")
print(f"  sleep_hours : 7")
print()
print(f"  Prediction  : {'PASS' if prediction[0] == 1 else 'FAIL'}")
print(f"  Confidence  : {max(probability[0]) * 100:.0f}%")
print()

plt.figure(figsize=(14, 6))
plot_tree(
    tree,
    feature_names=['study_hours', 'attendance', 'sleep_hours'],
    class_names=['FAIL', 'PASS'],
    filled=True,
    rounded=True,
    fontsize=11
)
plt.title(
    "Decision Tree",
    fontsize=14,
    fontweight='bold',
    pad=20
)
plt.tight_layout()
plt.savefig('decision_tree.png', dpi=150, bbox_inches='tight')
plt.close()
print("Tree diagram saved.")