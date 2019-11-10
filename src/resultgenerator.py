import os
import pickle
import pandas as pd

from util import Utils

abs_path = os.path.dirname(os.path.abspath(__file__))


def compute_predictions_for_age_group(X_test):
    model_path = os.path.join(abs_path, os.path.join("resources", "KNNlikes_age-group.sav"))
    loaded_model = pickle.load(open(model_path, 'rb'))
    y_pred = loaded_model.predict(X_test)
    pass


def compute_gender(test_data_path, df_results):
    model_path = os.path.join(abs_path, os.path.join("resources", "RandomForest_Gender.sav"))
    profile_df = Utils.read_data_to_dataframe(test_data_path + "/Profile/Profile.csv")
    profile_df.drop(profile_df.columns.difference(['userid', 'gender']), 1, inplace=True)
    image_df = Utils.read_data_to_dataframe(test_data_path + "/Image/oxford.csv")
    image_df.rename(columns={'userId': 'userid'}, inplace=True)

    merged_df = pd.merge(image_df, profile_df, on='userid')
    merged_df.drop(['userid', 'faceID', 'gender'], axis=1, inplace=True)
    model = Utils.read_pickle_from_file(model_path)

    model.predict(merged_df)
    image_df["gender"] = model.predict(merged_df)
    predicted_df = profile_df["userid"].to_frame()

    # image_df['userid'] = image_df['userid'].astype('|S')
    predicted_df = pd.merge(predicted_df, image_df, on="userid", how="left")
    user_gender_df = predicted_df.filter(["userid", "gender"])
    user_gender_df["gender"].fillna(1, inplace=True)
    user_gender_df = aggregate_duplicate_ids(user_gender_df, 'gender')


    df_results = pd.merge(df_results, user_gender_df, on='userid',how="left")
    df_results.drop(['gender_x'], axis=1, inplace=True)
    df_results.rename(columns={"gender_y": "gender"}, inplace=True)

    df_results.loc[df_results.gender == 0, 'gender'] = "male"
    df_results.loc[df_results.gender == 1, 'gender'] = "female"
    return df_results


def generate_df_for_all_users(profiles, model):
    profiles["age"] = model['age_group']
    profiles["gender"] = model['gender']
    profiles["ope"] = model['open']
    profiles["con"] = model['conscientious']
    profiles["ext"] = model['extrovert']
    profiles["agr"] = model['agreeable']
    profiles["neu"] = model['neurotic']
    return profiles


def compute_age(test_data_path, df_results):
    model_path = os.path.join(abs_path, os.path.join("resources", "KNNimages_age-group.sav"))
    profile_df = Utils.read_data_to_dataframe(test_data_path + "/Profile/Profile.csv")
    profile_df.drop(profile_df.columns.difference(['userid', 'age']), 1, inplace=True)
    image_df = Utils.read_data_to_dataframe(test_data_path + "/Image/oxford.csv")
    image_df.rename(columns={'userId': 'userid'}, inplace=True)
    merged_df = pd.merge(image_df, profile_df, on='userid')
    merged_df.drop(['userid', 'faceID', 'age'], axis=1, inplace=True)
    model = Utils.read_pickle_from_file(model_path)
    image_df["age_group"] = model.predict(merged_df)

    predicted_df = profile_df["userid"].to_frame()
    predicted_df = pd.merge(predicted_df, image_df, on='userid', how="left")
    user_age_df = predicted_df.filter(["userid", "age_group"])
    user_age_df["age_group"].fillna("xx-24", inplace=True)
    user_age_df = aggregate_duplicate_ids(user_age_df, 'age_group')
    df_results = pd.merge(df_results, user_age_df, on='userid')
    return df_results.drop(columns='age')


def compute_personality(test_data_path, df_results):
    return df_results


def aggregate_duplicate_ids(df, field_name):
    return df.groupby('userid', as_index=False)[field_name].agg(lambda x:x.value_counts().index[0])


class ResultGenerator:
    utils = Utils()

    def generate_results(self, test_data_path="../data/Public_Test/", path_to_results="../data/results"):
        """
        This method Run the test data against model/s and generated XML files
        """
        profiles_path = os.path.join(os.path.join(os.path.join(test_data_path, "Profile")), "Profile.csv")
        profiles = pd.read_csv(profiles_path)
        model_path = os.path.join(abs_path, os.path.join("resources", "model.json"))
        model = self.utils.read_json(model_path)
        df_results = generate_df_for_all_users(profiles, model)

        df_results = compute_gender(test_data_path, df_results)
        df_results = compute_age(test_data_path, df_results)
        df_results = compute_personality(test_data_path, df_results)

        xml_dictionary = self.generate_xml_from_profiles(df_results)
        self.store_individual_xmls_into_results_path(path_to_results, xml_dictionary, )

    @staticmethod
    def generate_xml_from_profiles(data_frame):
        """
      TODO this should be fixed
        """
        xml_dictionary = {}
        for index, row in data_frame.iterrows():
            xml = "<user \n id = \"" + row["userid"] + "\" " \
                                                       "\n age_group = \"" + str(
                row["age_group"]) + "\" \n gender = \"" + \
                  str(row["gender"]) + "\" \n extrovert = \"" + str(
                row["ext"]) + "\" \n neurotic = \"" + str(
                row["neu"]) + "\" \n agreeable = \"" + str(
                row["agr"]) + "\" \n conscientious = \"" + str(
                row[
                    "con"]) + "\" \n open = \"" + str(row["ope"]) + "\" />"
            xml_dictionary[row["userid"]] = xml

        return xml_dictionary

    def store_individual_xmls_into_results_path(self, path_to_results, xml_dictionary):
        """
        This method writes content of a dictionary into files choosing key as the nam eof the file
        """
        self.utils.make_directory_if_not_exists(path_to_results)
        for user in xml_dictionary:
            self.utils.write_to_directory(os.path.join(path_to_results, user + ".xml"), xml_dictionary[user])


if __name__ == "__main__":
    ResultGenerator().generate_results(test_data_path="../data/Public_Test/")
